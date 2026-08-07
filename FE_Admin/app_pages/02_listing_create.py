# 02_listing_create.py

import streamlit as st

from clients.listing_client import create_listing
from core.api_client import BackendAPIError
from core.auth import is_logged_in


st.title("청약정보 등록")

if not is_logged_in():
    st.warning("로그인이 필요합니다.")
    st.stop()

with st.form("listing_create_form", clear_on_submit=True):
    title = st.text_input("공고명")
    listing_type = st.selectbox("대상", ["공공임대", "분양", "기타"])
    location = st.text_input("위치")
    price = st.number_input("금액(원)", min_value=0, step=1000000)
    eligibility = st.text_area("자격 조건")
    announced_at = st.date_input("공고일")
    deadline = st.date_input("마감일")
    description = st.text_area("상세 설명")
    source_url = st.text_input("공고 원문 링크 (선택)", placeholder="예: https://apply.lh.or.kr/...")
    submitted = st.form_submit_button("등록", type="primary")

if submitted:
    if not title.strip():
        st.error("공고명을 입력해 주세요.")
    else:
        payload = {
            "title": title.strip(),
            "type": listing_type,
            "location": location.strip() or None,
            "price": int(price),
            "eligibility": eligibility.strip() or None,
            "announced_at": announced_at.isoformat(),
            "deadline": deadline.isoformat(),
            "description": description.strip() or None,
            "source_url": source_url.strip() or None,
        }
        try:
            result = create_listing(payload)
            if result.get("success"):
                st.success(result.get("message", "청약정보가 등록되었습니다."))
            else:
                st.error(result.get("message", "청약정보 등록에 실패했습니다."))
        except BackendAPIError as error:
            st.error(str(error))
