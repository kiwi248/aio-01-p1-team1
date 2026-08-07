# 02_listing_create.py

import streamlit as st

from clients.listing_client import create_listing
from core.api_client import BackendAPIError
from core.auth import is_logged_in
from core.constants import SEOUL_DISTRICTS


st.title("청약정보 등록")

if not is_logged_in():
    st.warning("로그인이 필요합니다.")
    st.stop()

with st.form("listing_create_form", clear_on_submit=True):
    title = st.text_input("공고 제목")
    housing_name = st.text_input("주택명")
    area_sqm = st.number_input("면적(㎡)", min_value=0.01)
    recruitment_count = st.number_input("모집 인원", min_value=1, step=1)
    location = st.selectbox(
        "지역(서울 자치구)",
        SEOUL_DISTRICTS,
        index=None,
        placeholder="자치구를 선택해 주세요",
    )
    deposit = st.number_input("보증금", min_value=0, step=10000)
    monthly_rent = st.number_input("월세", min_value=0, step=10000)
    application_start_date = st.date_input("신청 시작일")
    application_end_date = st.date_input("신청 종료일")
    description = st.text_area("상세 설명")
    image_url = st.text_input("이미지 URL(선택)")
    source_url = st.text_input("원문 URL", placeholder="예: https://apply.lh.or.kr/...")
    submitted = st.form_submit_button("등록", type="primary")

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
            "image_url": image_url.strip() or None,
            "source_url": source_url.strip(),
        }
        try:
            result = create_listing(payload)
            if result.get("success"):
                st.success(result.get("message", "청약정보가 등록되었습니다."))
            else:
                st.error(result.get("message", "청약정보 등록에 실패했습니다."))
        except BackendAPIError as error:
            st.error(str(error))
