# 03_listings.py

import streamlit as st

from clients.favorite_client import create_favorite
from clients.listing_client import get_listings, search_listings
from core.api_client import BackendAPIError
from core.auth import is_logged_in
from core.area_format import format_area
from core.constants import SEOUL_DISTRICTS
from core.dday import dday_label, dim_if_closed, is_closed
from core.pagination import (
    PAGE_SIZE,
    build_params,
    clamp_page,
    parse_page,
    slice_page,
    total_pages,
)


st.title("청약정보 조회")

if message := st.session_state.pop("listing_message", None):
    st.success(message)

# 지금 보고 있는 페이지는 주소창에 둡니다.
# 새로고침해도 보던 페이지가 그대로 나오게 하려는 것입니다.
current_page = parse_page(st.query_params.get_all("page"))


def go_to_page(page: int) -> None:
    """페이지를 옮깁니다. 값이 같으면 주소를 다시 쓰지 않습니다."""
    target = build_params(page)
    if st.query_params.to_dict() != target:
        st.query_params.from_dict(target)
    st.rerun()

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
        total_count = len(listings)

        if search_submitted:
            # 검색 결과는 관리자 화면과 같이 한 번에 모두 보여 줍니다.
            page = last_page = None
            page_items = listings
            st.caption(f"검색 결과 {total_count}건 (마감이 가까운 순)")
        else:
            last_page = total_pages(total_count, PAGE_SIZE)
            page = clamp_page(current_page, total_count, PAGE_SIZE)
            page_items = slice_page(listings, page, PAGE_SIZE)

            # 공고가 줄어 페이지가 사라진 경우 주소창도 함께 맞춰 둡니다.
            if page != current_page:
                go_to_page(page)

            st.caption(
                f"총 {total_count}건  |  {page} / {last_page} 페이지 (마감이 가까운 순)"
            )

        for listing in page_items:
            end_date = listing.get("application_end_date")
            closed = is_closed(end_date)
            remaining = dday_label(end_date)

            # 신청이 끝난 공고는 글자를 흐린 회색으로 두어 한눈에 구분되게 합니다.
            def dim(text: object) -> str:
                return dim_if_closed(text, closed)

            with st.container(border=True):
                st.markdown(f"### {dim(listing.get('title') or '제목 없음')}")
                if listing.get("image_url"):
                    st.image(listing["image_url"], width=300)
                st.markdown(
                    dim(
                        f"주택명: {listing.get('housing_name') or '-'}  |  "
                        f"자치구: {listing.get('location') or '-'}"
                    )
                )
                if listing.get("detail_address"):
                    st.markdown(dim(f"주소: {listing['detail_address']}"))
                st.markdown(
                    dim(
                        f"면적: {format_area(listing.get('area_sqm'))}  |  "
                        f"모집 인원: {listing.get('recruitment_count') or '-'}명"
                    )
                )
                st.markdown(
                    dim(
                        f"보증금: {int(listing.get('deposit') or 0):,}원  |  "
                        f"월세: {int(listing.get('monthly_rent') or 0):,}원"
                    )
                )
                st.caption(
                    f"신청 기간: {listing.get('application_start_date') or '-'} ~ "
                    f"{end_date or '-'}"
                )
                if remaining:
                    if closed:
                        st.caption(f"신청 마감 ({remaining})")
                    else:
                        st.warning(f"신청 마감까지 {remaining}")
                if listing.get("description"):
                    st.markdown(dim(listing["description"]))

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

        # 검색 결과일 때는 페이지 이동 버튼을 두지 않습니다.
        if last_page is not None:
            st.divider()
            previous_column, input_column, go_column, next_column, info_column = st.columns(
                [1, 1.2, 1, 1, 2]
            )

            with previous_column:
                if st.button(
                    "이전", disabled=page <= 1, use_container_width=True, key="user-page-prev"
                ):
                    go_to_page(page - 1)

            with input_column:
                # key에 현재 페이지를 넣어 두면 페이지가 바뀔 때마다 입력창이 새로 만들어집니다.
                target_page = st.number_input(
                    "페이지 번호",
                    min_value=1,
                    max_value=last_page,
                    value=page,
                    step=1,
                    label_visibility="collapsed",
                    key=f"user-page-input-{page}-{last_page}",
                )

            with go_column:
                if st.button("이동", use_container_width=True, key="user-page-go"):
                    go_to_page(int(target_page))

            with next_column:
                if st.button(
                    "다음",
                    disabled=page >= last_page,
                    use_container_width=True,
                    key="user-page-next",
                ):
                    go_to_page(page + 1)

            with info_column:
                st.caption(f"현재 {page} / {last_page} 페이지")
except BackendAPIError as error:
    st.error(str(error))
