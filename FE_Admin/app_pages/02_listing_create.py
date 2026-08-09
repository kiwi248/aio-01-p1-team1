# 02_listing_create.py

import streamlit as st

from clients.listing_client import create_listing, upload_listing_image
from core.api_client import BackendAPIError
from core.auth import is_logged_in
from core.constants import SEOUL_DISTRICTS
from core.create_form import reset_form_state


# 이미지 크기 제한입니다. 백엔드에서도 같은 값으로 다시 검사합니다.
MAX_IMAGE_SIZE = 5 * 1024 * 1024

st.title("청약정보 등록")

if not is_logged_in():
    st.warning("로그인이 필요합니다.")
    st.stop()

# 비슷한 공고를 이어서 넣는 일이 많아, 등록한 뒤에도 입력값을 지우지 않습니다.
# 아예 새 공고를 넣을 때는 폼 아래의 "입력 초기화" 버튼을 씁니다.
with st.form("listing_create_form", clear_on_submit=False):
    title = st.text_input("공고 제목", key="create-title")
    housing_name = st.text_input("주택명", key="create-housing-name")
    area_sqm = st.number_input("면적(㎡)", min_value=0.01, key="create-area-sqm")
    recruitment_count = st.number_input(
        "모집 인원", min_value=1, step=1, key="create-recruitment-count"
    )
    location = st.selectbox(
        "지역(서울 자치구)",
        SEOUL_DISTRICTS,
        index=None,
        placeholder="자치구를 선택해 주세요",
        key="create-location",
    )
    deposit = st.number_input("보증금", min_value=0, step=10000, key="create-deposit")
    monthly_rent = st.number_input(
        "월세", min_value=0, step=10000, key="create-monthly-rent"
    )
    application_start_date = st.date_input("신청 시작일", key="create-start-date")
    application_end_date = st.date_input("신청 종료일", key="create-end-date")
    description = st.text_area("상세 설명", key="create-description")
    image_file = st.file_uploader(
        "이미지 (선택, 최대 5MB)",
        type=["jpg", "jpeg", "png", "webp"],
        key="create-image",
    )
    source_url = st.text_input(
        "원문 URL", placeholder="예: https://apply.lh.or.kr/...", key="create-source-url"
    )
    submitted = st.form_submit_button("등록", type="primary")

st.caption("등록해도 입력한 내용이 그대로 남습니다. 비슷한 공고를 이어서 넣을 때 편합니다.")

# 초기화는 폼 밖에 둡니다. 폼 안에 두면 등록과 함께 눌러야 하기 때문입니다.
if st.button("입력 초기화", key="create-reset"):
    reset_form_state(st.session_state)
    st.rerun()

if submitted:
    if not (
        title.strip()
        and housing_name.strip()
        and location
        and description.strip()
        and source_url.strip()
    ):
        st.error("공고 제목, 주택명, 자치구, 상세 설명, 원문 URL을 모두 입력해 주세요.")
    elif application_end_date < application_start_date:
        st.error("신청 종료일은 신청 시작일보다 빠를 수 없습니다.")
    elif image_file is not None and image_file.size > MAX_IMAGE_SIZE:
        st.error(
            f"이미지 크기는 5MB를 넘을 수 없습니다. "
            f"(선택한 파일: {image_file.size / 1024 / 1024:.1f}MB) "
            f"크기를 줄이거나 이미지를 빼고 등록해 주세요."
        )
    else:
        payload = {
            "title": title.strip(),
            "housing_name": housing_name.strip(),
            "area_sqm": float(area_sqm),
            "recruitment_count": int(recruitment_count),
            "location": location,
            "deposit": int(deposit),
            "monthly_rent": int(monthly_rent),
            "application_start_date": application_start_date.isoformat(),
            "application_end_date": application_end_date.isoformat(),
            "description": description.strip(),
            "image_url": None,
            "source_url": source_url.strip(),
        }
        try:
            # 이미지를 고른 경우에만 먼저 업로드하고, 받은 URL을 payload에 넣습니다.
            if image_file is not None:
                with st.spinner("이미지를 업로드하는 중..."):
                    upload_result = upload_listing_image(image_file)
                payload["image_url"] = (upload_result.get("data") or {}).get("image_url")

            result = create_listing(payload)
            if result.get("success"):
                st.success(result.get("message", "청약정보가 등록되었습니다."))
            else:
                st.error(result.get("message", "청약정보 등록에 실패했습니다."))
        except BackendAPIError as error:
            st.error(str(error))
