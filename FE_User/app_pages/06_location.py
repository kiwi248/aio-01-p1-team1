import streamlit as st
from clients.listing_client import get_listings
from clients.location_client import (
    geocode_location,
    get_nearby_facilities,
)
from core.api_client import BackendAPIError


DEFAULT_RADIUS_M = 2000
DEFAULT_FACILITY_LIMIT = 3

RADIUS_OPTIONS = {
    "1km": 1000,
    "2km": 2000,
    "3km": 3000,
}


def format_distance(distance_m: int) -> str:
    """미터 거리를 화면에 읽기 좋은 문자열로 바꿉니다."""

    if distance_m >= 1000:
        return f"{distance_m / 1000:.1f}km"

    return f"{distance_m}m"


def listing_search_text(listing: dict) -> str:
    """공고에서 검색에 사용할 제목과 주소를 하나의 문자열로 만듭니다."""

    title = str(listing.get("title") or "")
    detail_address = str(listing.get("detail_address") or "")

    return f"{title} {detail_address}".lower()


def find_matching_listings(
    listings: list[dict],
    query: str,
) -> list[dict]:
    """입력한 문구가 공고명 또는 공고주소에 들어 있는 공고만 찾습니다."""

    normalized_query = query.strip().lower()

    if not normalized_query:
        return []

    return [
        listing
        for listing in listings
        if normalized_query in listing_search_text(listing)
    ]


def listing_label(listing: dict) -> str:
    """검색된 공고를 선택 목록에 표시할 문자열을 만듭니다."""

    title = str(listing.get("title") or "공고명 없음")
    detail_address = str(
        listing.get("detail_address") or "상세주소 없음"
    )

    return f"{title} | {detail_address}"

st.title("생활권 분석")
st.caption(
    "청약정보에 등록된 공고명 또는 공고주소를 검색하면 "
    "주변 지하철역·마트·병원 정보를 알려드립니다."
)


with st.form("location-search-form"):
    query = st.text_input(
        "공고명 또는 공고주소",
        placeholder="예: 행복주택 입주자 모집공고",
    )

    selected_radius = st.selectbox(
        "생활권 검색 반경",
        options=list(RADIUS_OPTIONS),
        index=1,
    )

    submitted = st.form_submit_button(
        "주변생활권 탐색",
        type="primary",
        use_container_width=True,
    )


if submitted:
    query = query.strip()

    if not query:
        st.warning("공고명 또는 공고주소를 입력해 주세요.")
        st.stop()

    try:
        with st.spinner("청약정보에서 공고를 검색하는 중입니다..."):
            listing_response = get_listings()
            all_listings = listing_response.get("data") or []
    except BackendAPIError as error:
        st.error(str(error))
        st.stop()

    matching_listings = find_matching_listings(
        listings=all_listings,
        query=query,
    )

    if not matching_listings:
        st.session_state.pop("location-search-matches", None)
        st.error(
            "청약정보 내에서 일치하는 공고를 찾을 수 없습니다. "
            "공고명 또는 공고주소를 다시 확인해 주세요."
        )
        st.stop()

    st.session_state["location-search-matches"] = matching_listings
    st.session_state["location-search-radius"] = RADIUS_OPTIONS.get(
        selected_radius,
        DEFAULT_RADIUS_M,
    )
    st.session_state["location-search-radius-label"] = selected_radius


matching_listings = st.session_state.get(
    "location-search-matches",
    [],
)

if matching_listings:
    selected_listing = st.selectbox(
        "분석할 공고 선택",
        options=matching_listings,
        format_func=listing_label,
    )

    listing_address = str(
        selected_listing.get("detail_address") or ""
    ).strip()

    if not listing_address:
        st.error(
            "선택한 공고에 상세주소가 등록되어 있지 않아 "
            "생활권을 분석할 수 없습니다."
        )
        st.stop()

    radius_m = st.session_state.get(
        "location-search-radius",
        DEFAULT_RADIUS_M,
    )
    search_radius_label = st.session_state.get(
        "location-search-radius-label",
        "2km",
    )

    try:
        with st.spinner("공고 주소와 주변 지하철역을 검색하는 중입니다..."):
            location_response = geocode_location(listing_address)
            location = location_response.get("data") or {}

            latitude = location.get("latitude")
            longitude = location.get("longitude")

            if latitude is None or longitude is None:
                st.error("공고 주소의 좌표를 확인할 수 없습니다.")
                st.stop()

            subway_response = get_nearby_subways(
                latitude=latitude,
                longitude=longitude,
                radius_m=radius_m,
                limit=DEFAULT_STATION_LIMIT,
            )
            stations = subway_response.get("data") or []
    except BackendAPIError as error:
        st.error(str(error))
        st.stop()

    st.subheader("선택한 공고")
    st.write(selected_listing.get("title") or "공고명 없음")
    st.caption(location.get("address") or listing_address)

    st.divider()
    st.subheader("가까운 지하철역")

    if not stations:
        st.info(
            f"반경 {search_radius_label} 안에서 "
            "지하철역을 찾지 못했습니다."
        )
    else:
        for index, station in enumerate(stations, start=1):
            distance_m = int(station.get("distance_m") or 0)
            walking_minutes = int(
                station.get("estimated_walking_minutes") or 1
            )

            with st.container(border=True):
                st.markdown(
                    f"### {index}. "
                    f"{station.get('name') or '이름 없는 역'}"
                )

                station_address = station.get("address") or ""

                if station_address:
                    st.write(station_address)

                st.write(
                    f"직선거리 {format_distance(distance_m)} · "
                    f"예상 도보 약 {walking_minutes}분"
                )

    st.caption(
        "※ 도보시간은 직선거리에 보정값을 적용한 예상치입니다. "
        "실제 경로, 횡단보도 및 출입구 위치에 따라 달라질 수 있습니다."
    )