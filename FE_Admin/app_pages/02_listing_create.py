# 02_listing_create.py

import streamlit as st

from clients.listing_client import create_listing, upload_listing_image
from core.amount_format import describe_amount
from core.api_client import BackendAPIError
from core.auth import is_logged_in
from core.constants import SEOUL_DISTRICTS
from core.create_form import current_nonce, field_key, reset_form_state


# 이미지 크기 제한입니다. 백엔드에서도 같은 값으로 다시 검사합니다.
MAX_IMAGE_SIZE = 5 * 1024 * 1024

st.title("청약정보 등록")

if not is_logged_in():
    st.warning("로그인이 필요합니다.")
    st.stop()

# 지금 폼 번호입니다. 초기화를 누르면 번호가 올라가 입력칸이 새로 만들어집니다.
nonce = current_nonce(st.session_state)

st.caption("등록해도 입력한 내용이 그대로 남습니다. 비슷한 공고를 이어서 넣을 때 편합니다.")

# st.form으로 묶지 않습니다.
# 폼 안에서는 등록을 누르기 전까지 화면이 다시 그려지지 않아,
# 보증금과 월세를 입력하는 동안 얼마인지 확인할 수 없기 때문입니다.
title = st.text_input("공고 제목", key=field_key("title", nonce))
housing_name = st.text_input("주택명", key=field_key("housing-name", nonce))
area_sqm = st.number_input("면적(㎡)", min_value=0.01, key=field_key("area-sqm", nonce))
recruitment_count = st.number_input(
    "모집 인원", min_value=1, step=1, key=field_key("recruitment-count", nonce)
)
location = st.selectbox(
    "지역(서울 자치구)",
    SEOUL_DISTRICTS,
    index=None,
    placeholder="자치구를 선택해 주세요",
    key=field_key("location", nonce),
)
detail_address = st.text_input(
    "상세주소 (선택)",
    placeholder="예: 서울 강남구 도곡로 464",
    key=field_key("detail-address", nonce),
)

deposit = st.number_input(
    "보증금", min_value=0, step=10000, key=field_key("deposit", nonce)
)
# 0이 몇 개인지 세지 않아도 되도록 쉼표와 만·억 단위 읽기를 함께 보여 줍니다.
st.caption(describe_amount(deposit))

monthly_rent = st.number_input(
    "월세", min_value=0, step=10000, key=field_key("monthly-rent", nonce)
)
st.caption(describe_amount(monthly_rent))

application_start_date = st.date_input("신청 시작일", key=field_key("start-date", nonce))
application_end_date = st.date_input("신청 종료일", key=field_key("end-date", nonce))
description = st.text_area("상세 설명", key=field_key("description", nonce))
image_file = st.file_uploader(
    "이미지 (선택, 최대 5MB)",
    type=["jpg", "jpeg", "png", "webp"],
    key=field_key("image", nonce),
)
source_url = st.text_input(
    "원문 URL",
    placeholder="예: https://apply.lh.or.kr/...",
    key=field_key("source-url", nonce),
)

# 두 버튼을 나란히 둡니다.
submit_column, reset_column = st.columns(2)

with submit_column:
    submitted = st.button("등록", type="primary", use_container_width=True, key="create-submit")

with reset_column:
    reset_clicked = st.button("입력 초기화", use_container_width=True, key="create-reset")

if reset_clicked:
    # 값을 지우고 폼 번호를 올려 입력칸을 새로 만듭니다.
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
            "detail_address": detail_address.strip() or None,
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
