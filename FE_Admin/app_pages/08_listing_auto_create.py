# 08_listing_auto_create.py
"""공고 PDF를 Gemini에 보내 청약정보를 뽑아내고, 확인한 뒤 등록합니다.

뽑아낸 값을 바로 저장하지 않습니다. 관리자가 화면에서 확인하고 고른 건만
기존 청약정보 등록 API로 보냅니다.
"""

import streamlit as st

from clients.gemini_client import GeminiError, extract_listings_from_pdf
from clients.listing_client import create_listing
from core.api_client import BackendAPIError
from core.auth import is_logged_in
from core.constants import SEOUL_DISTRICTS
from core.gemini_config import get_model_name, has_api_key
from core.listing_extract import summarize, validate_all


# 공고 PDF 크기 제한입니다. 너무 큰 파일은 모델이 처리하지 못합니다.
MAX_PDF_SIZE = 20 * 1024 * 1024

st.title("청약정보 등록(자동)")

if not is_logged_in():
    st.warning("로그인이 필요합니다.")
    st.stop()

st.caption(
    "공고 PDF를 올리면 Gemini가 청약정보를 뽑아냅니다. "
    "뽑아낸 값은 바로 저장되지 않으며, 확인하고 고른 건만 등록합니다."
)

if not has_api_key():
    st.error(
        "Gemini API 키가 없어 자동 추출을 쓸 수 없습니다.\n\n"
        "`FE_Admin/.env` 파일에 `GEMINI_API_KEY=발급받은키` 를 넣고 화면을 새로고침해 주세요."
    )
    st.info("키를 넣기 전까지는 `청약정보 등록(수동)` 화면을 이용해 주세요.")
    st.stop()

st.caption(f"사용 모델: {get_model_name()}")

pdf_file = st.file_uploader("공고 PDF", type=["pdf"], key="auto-pdf")

if st.button("PDF에서 청약정보 뽑아내기", type="primary", disabled=pdf_file is None):
    if pdf_file.size > MAX_PDF_SIZE:
        st.error(
            f"PDF 크기는 20MB를 넘을 수 없습니다. (선택한 파일: {pdf_file.size / 1024 / 1024:.1f}MB)"
        )
    else:
        try:
            with st.spinner("Gemini가 공고를 읽는 중입니다..."):
                extracted = extract_listings_from_pdf(pdf_file.getvalue(), pdf_file.name)
            st.session_state.auto_extracted = extracted
            st.session_state.auto_source_name = pdf_file.name
        except GeminiError as error:
            st.error(str(error))

extracted = st.session_state.get("auto_extracted")

if not extracted:
    st.stop()

results = validate_all(extracted, SEOUL_DISTRICTS)
counts = summarize(results)

st.divider()
st.subheader(f"추출 결과 {counts['total']}건")

ready_column, blocked_column = st.columns(2)
ready_column.metric("등록 가능", f"{counts['ready']}건")
blocked_column.metric("확인 필요", f"{counts['blocked']}건")

if counts["blocked"]:
    st.warning(
        "값이 비어 있거나 형식이 맞지 않는 건이 있습니다. "
        "그 건은 등록하지 않고, `청약정보 등록(수동)` 화면에서 직접 넣어 주세요."
    )

selected_indexes = []

for result in results:
    source = result["source"]
    label = source.get("housing_name") or source.get("title") or f"{result['index'] + 1}번째 항목"

    with st.container(border=True):
        if result["problems"]:
            st.markdown(f"**{label}** — 확인 필요")
            for problem in result["problems"]:
                st.caption(f"• {problem}")
        else:
            payload = result["payload"]
            checked = st.checkbox(
                f"{label}", value=True, key=f"auto-pick-{result['index']}"
            )
            if checked:
                selected_indexes.append(result["index"])
            st.caption(
                f"{payload['location']}  ·  전용 {payload['area_sqm']}㎡  ·  "
                f"{payload['recruitment_count']}호 모집"
            )
            st.caption(
                f"보증금 {payload['deposit']:,}원  |  월세 {payload['monthly_rent']:,}원  |  "
                f"신청 {payload['application_start_date']} ~ {payload['application_end_date']}"
            )

        with st.expander("뽑아낸 원본 값 보기"):
            st.json(source)

st.divider()

if st.button(
    f"선택한 {len(selected_indexes)}건 등록",
    type="primary",
    disabled=not selected_indexes,
):
    by_index = {result["index"]: result for result in results}
    succeeded, failed = [], []

    with st.spinner("등록하는 중..."):
        for index in selected_indexes:
            payload = by_index[index]["payload"]
            label = payload["housing_name"]
            try:
                response = create_listing(payload)
                if response.get("success"):
                    succeeded.append(label)
                else:
                    failed.append((label, response.get("message", "등록에 실패했습니다.")))
            except BackendAPIError as error:
                failed.append((label, str(error)))
                # 한 건이라도 실패하면 멈춥니다. 남은 건은 원인을 확인한 뒤 다시 시도합니다.
                break

    if succeeded:
        st.success(f"{len(succeeded)}건을 등록했습니다.")
        for name in succeeded:
            st.caption(f"• {name}")

    if failed:
        st.error(f"{len(failed)}건을 등록하지 못했습니다.")
        for name, reason in failed:
            st.caption(f"• {name}: {reason}")

    if succeeded and not failed:
        # 같은 PDF를 두 번 등록하지 않도록 결과를 비웁니다.
        st.session_state.pop("auto_extracted", None)

if st.button("추출 결과 지우기", key="auto-clear"):
    st.session_state.pop("auto_extracted", None)
    st.session_state.pop("auto_source_name", None)
    st.rerun()
