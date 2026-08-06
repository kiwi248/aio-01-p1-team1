# 03_listing_manage.py

import streamlit as st

from clients.listing_client import delete_listing, get_listings, search_listings
from core.api_client import BackendAPIError
from core.auth import is_logged_in


st.title("청약정보 조회 / 삭제")

if not is_logged_in():
    st.warning("로그인이 필요합니다.")
    st.stop()

if message := st.session_state.pop("listing_message", None):
    st.success(message)

with st.expander("조건검색"):
    with st.form("listing_search_form"):
        search_type = st.text_input("대상", placeholder="예: 공공임대")
        search_location = st.text_input("위치", placeholder="예: 강남구")
        search_min_price = st.number_input("최소 금액", min_value=0, step=1000000, value=0)
        search_max_price = st.number_input("최대 금액", min_value=0, step=1000000, value=0)
        search_eligibility = st.text_input("자격 조건", placeholder="예: 무주택")
        search_submitted = st.form_submit_button("검색")

try:
    if search_submitted:
        params = {
            "type": search_type.strip() or None,
            "location": search_location.strip() or None,
            "min_price": int(search_min_price) or None,
            "max_price": int(search_max_price) or None,
            "eligibility": search_eligibility.strip() or None,
        }
        with st.spinner("검색 중..."):
            response = search_listings(params)
    else:
        with st.spinner("불러오는 중..."):
            response = get_listings()

    listings = response.get("data") or []

    if not listings:
        st.info("조회된 청약정보가 없습니다.")
    else:
        st.caption(f"총 {len(listings)}건")

        for listing in listings:
            with st.container(border=True):
                st.subheader(listing.get("title") or "제목 없음")
                st.write(
                    f"대상: {listing.get('type') or '-'}  |  "
                    f"위치: {listing.get('location') or '-'}  |  "
                    f"금액: {int(listing.get('price') or 0):,}원"
                )
                st.write(f"자격 조건: {listing.get('eligibility') or '-'}")
                st.caption(
                    f"공고일: {listing.get('announced_at') or '-'}  |  "
                    f"마감일: {listing.get('deadline') or '-'}"
                )
                if listing.get("description"):
                    st.write(listing["description"])

                delete_confirmed = st.checkbox(
                    "삭제한 청약정보는 복구할 수 없습니다. 삭제에 동의합니다.",
                    key=f"delete-confirm-{listing['id']}",
                )
                if st.button(
                    "삭제",
                    type="primary",
                    disabled=not delete_confirmed,
                    key=f"delete-listing-{listing['id']}",
                ):
                    result = delete_listing(listing["id"])
                    st.session_state.listing_message = result.get(
                        "message", "청약정보를 삭제했습니다."
                    )
                    st.rerun()
except BackendAPIError as error:
    st.error(str(error))
