import streamlit as st

from clients.location_client import (
    geocode_location,
    get_nearby_subways,
)
from core.api_client import BackendAPIError


DEFAULT_RADIUS_M = 2000
DEFAULT_STATION_LIMIT = 3

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


st.title("생활권 분석")
st.caption(
    "공고의 상세주소나 주택명을 입력하면 "
    "주변 지하철역과 예상 도보시간을 알려드립니다."
)

with st.form("location-search-form"):
    query = st.text_input(
        "공고 주소 또는 주택명",
        placeholder="예: 서울특별시 중구 세종대로 110",
    )

    selected_radius = st.selectbox(
        "지하철역 검색 반경",
        options=list(RADIUS_OPTIONS),
        index=1,
    )

    submitted = st.form_submit_button(
        "주변 지하철역 찾기",
        type="primary",
        use_container_width=True,
    )


if submitted:
    query = query.strip()

    if not query:
        st.warning("공고 주소 또는 주택명을 입력해 주세요.")
        st.stop()

    radius_m = RADIUS_OPTIONS.get(
        selected_radius,
        DEFAULT_RADIUS_M,
    )

    try:
        with st.spinner("주소와 주변 지하철역을 검색하는 중입니다..."):
            location_response = geocode_location(query)
            location = location_response.get("data") or {}

            latitude = location.get("latitude")
            longitude = location.get("longitude")

            if latitude is None or longitude is None:
                st.error("검색 결과에서 좌표를 확인할 수 없습니다.")
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

    st.subheader("검색 위치")
    st.write(location.get("address") or query)

    if location.get("matched_by") == "keyword":
        st.warning(
            "장소명으로 검색한 첫 번째 결과입니다. "
            "표시된 주소가 맞는지 확인해 주세요."
        )

    st.divider()
    st.subheader("가까운 지하철역")

    if not stations:
        st.info(
            f"반경 {selected_radius} 안에서 "
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