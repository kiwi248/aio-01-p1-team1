import os
from pathlib import Path

import httpx
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
KAKAO_ADDRESS_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/address.json"


def get_kakao_rest_api_key() -> str:
    """배포 환경은 secrets, 로컬 환경은 FE_User/.env에서 REST API 키를 읽습니다."""

    try:
        value = st.secrets["KAKAO_REST_API_KEY"]
    except Exception:
        load_dotenv(ENV_PATH)
        value = os.getenv("KAKAO_REST_API_KEY", "")
    return (value or "").strip()


@st.cache_data(show_spinner=False)
def geocode_address(address: str, rest_api_key: str) -> tuple[float, float] | None:
    """카카오 주소 검색 REST API로 주소를 위도와 경도로 변환합니다."""

    response = httpx.get(
        KAKAO_ADDRESS_SEARCH_URL,
        params={"query": address},
        headers={"Authorization": f"KakaoAK {rest_api_key}"},
        timeout=5.0,
    )
    response.raise_for_status()

    documents = response.json().get("documents") or []
    if not documents:
        return None

    first_result = documents[0]
    return float(first_result["y"]), float(first_result["x"])


def render_favorite_map(favorites: list[dict], rest_api_key: str) -> None:
    """즐겨찾기 공고 주소를 좌표로 변환해 지도에 표시합니다."""

    if not rest_api_key or rest_api_key.startswith("your-"):
        st.info("지도를 표시하려면 FE_User/.env에 KAKAO_REST_API_KEY를 설정해 주세요.")
        return

    points = []
    failed_locations = []

    with st.spinner("즐겨찾기 위치를 찾는 중입니다..."):
        
        for favorite in favorites:
            listing = favorite.get("listing") or {}
            location = (listing.get("detail_address") or listing.get("detail_address") or "").strip()
            if not location:
                continue

            try:
                coordinates = geocode_address(location, rest_api_key)
            except (httpx.HTTPError, KeyError, TypeError, ValueError):
                failed_locations.append(location)
                continue

            if coordinates is None:
                failed_locations.append(location)
                continue

            latitude, longitude = coordinates
            points.append(
                {
                    "title": listing.get("title") or "제목 없음",
                    "location": location,
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )

    if not points:
        st.info("지도에 표시할 수 있는 위치 정보가 없습니다.")
        return

    map_data = pd.DataFrame(points)
    st.map(
        map_data,
        use_container_width=True,
    )

    if failed_locations:
        st.caption(f"좌표를 찾지 못한 위치: {len(failed_locations)}건")
