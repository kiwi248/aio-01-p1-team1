# 03_listings.py

import streamlit as st

from clients.favorite_client import create_favorite
from clients.listing_client import get_listings, search_listings
from core.api_client import BackendAPIError
from core.auth import is_logged_in
from core.constants import SEOUL_DISTRICTS
from core.listing_view import (
    card_title,
    description_preview,
    format_won,
    period_line,
    summary_line,
)


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
        st.caption(f"총 {len(listings)}건 (최신순)")

        for listing in listings:
            with st.container(border=True):
                # 같은 공고 안에 주택형이 여러 개라 공고명이 전부 같습니다.
                # 그래서 주택명을 앞세우고 공고명은 작게 둡니다.
                text_column, image_column = st.columns([3, 1], vertical_alignment="top")

                with text_column:
                    st.markdown(f"#### {card_title(listing)}")
                    st.caption(listing.get("title") or "")
                    summary = summary_line(listing)
                    if summary:
                        st.write(summary)

                with image_column:
                    if listing.get("image_url"):
                        st.image(listing["image_url"], use_container_width=True)

                # 금액은 가장 먼저 보게 되는 값이라 따로 크게 보여 줍니다.
                deposit_column, rent_column = st.columns(2)
                deposit_column.metric("보증금", format_won(listing.get("deposit")))
                rent_column.metric("월세", format_won(listing.get("monthly_rent")))

                st.caption(period_line(listing))

                # 설명이 길어 목록이 늘어지므로 첫 줄만 보여 주고 접어 둡니다.
                preview = description_preview(listing)
                if preview:
                    with st.expander(f"상세 정보  ·  {preview}"):
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
