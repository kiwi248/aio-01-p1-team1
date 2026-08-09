# 03_listings.py

import streamlit as st

from clients.favorite_client import create_favorite
from clients.listing_client import get_listings, search_listings
from core.api_client import BackendAPIError
from core.auth import is_logged_in
from core.constants import SEOUL_DISTRICTS
from core.listing_sort import DEFAULT_SORT, SORT_OPTIONS, sort_listings


st.title("청약정보 조회")

if message := st.session_state.pop("listing_message", None):
    st.success(message)

with st.expander("조건검색"):
    with st.form("listing_search_form"):
        search_location = st.selectbox("서울 자치구", ("전체",) + SEOUL_DISTRICTS)
        search_max_deposit = st.number_input("최대 보증금", min_value=0, step=10000, value=0)
        search_max_monthly_rent = st.number_input("최대 월세", min_value=0, step=10000, value=0)
        search_submitted = st.form_submit_button("검색")

try:
    if search_submitted:
        params = {}
        if search_location != "전체":
            params["location"] = search_location
        if int(search_max_deposit) > 0:
            params["max_deposit"] = int(search_max_deposit)
        if int(search_max_monthly_rent) > 0:
            params["max_monthly_rent"] = int(search_max_monthly_rent)
        with st.spinner("검색 중..."):
            response = search_listings(params)
    else:
        with st.spinner("불러오는 중..."):
            response = get_listings()

    listings = response.get("data") or []

    if not listings:
        st.info("조회된 청약정보가 없습니다.")
    else:
        # 정렬은 화면에서 다시 늘어놓습니다. 서버에 다시 묻지 않습니다.
        sort_option = st.selectbox(
            "정렬 기준",
            SORT_OPTIONS,
            index=SORT_OPTIONS.index(DEFAULT_SORT),
            key="listing-sort",
        )
        listings = sort_listings(listings, sort_option)

        st.caption(f"총 {len(listings)}건 ({sort_option})")

        for listing in listings:
            with st.container(border=True):
                st.subheader(listing.get("title") or "제목 없음")
                if listing.get("image_url"):
                    st.image(listing["image_url"], width=300)
                st.write(
                    f"주택명: {listing.get('housing_name') or '-'}  |  "
                    f"자치구: {listing.get('location') or '-'}"
                )
                st.write(
                    f"면적: {listing.get('area_sqm') or '-'}㎡  |  "
                    f"모집 인원: {listing.get('recruitment_count') or '-'}명"
                )
                st.write(
                    f"보증금: {int(listing.get('deposit') or 0):,}원  |  "
                    f"월세: {int(listing.get('monthly_rent') or 0):,}원"
                )
                st.caption(
                    f"신청 기간: {listing.get('application_start_date') or '-'} ~ "
                    f"{listing.get('application_end_date') or '-'}"
                )
                if listing.get("description"):
                    st.write(listing["description"])

                if listing.get("source_url"):
                    st.link_button("공고 원문 보기", listing["source_url"])

                if is_logged_in():
                    if st.button("즐겨찾기 추가", key=f"favorite-add-{listing['id']}"):
                        result = create_favorite(st.session_state.user_id, listing["id"])
                        st.session_state.listing_message = result.get(
                            "message", "즐겨찾기에 등록되었습니다."
                        )
                        st.rerun()
                else:
                    st.caption("로그인하면 즐겨찾기에 담을 수 있습니다.")
except BackendAPIError as error:
    st.error(str(error))
