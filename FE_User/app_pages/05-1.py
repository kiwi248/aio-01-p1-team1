import json
import os
from pathlib import Path
from urllib.parse import quote

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from clients.favorite_client import delete_favorite, get_mypage_favorites
from core.api_client import BackendAPIError
from core.auth import is_logged_in

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"


def get_kakao_javascript_key() -> str:
    """배포 환경은 secrets, 로컬 환경은 FE_User/.env에서 지도 키를 읽습니다."""

    try:
        value = st.secrets["KAKAO_JAVASCRIPT_KEY"]
    except Exception:
        load_dotenv(ENV_PATH)
        value = os.getenv("KAKAO_JAVASCRIPT_KEY", "")
    return (value or "").strip()


def render_favorite_map(favorites: list[dict], javascript_key: str) -> None:
    """즐겨찾기 공고의 위치만 카카오 지도에 별표로 표시합니다."""

    places = []
    for favorite in favorites:
        listing = favorite.get("listing") or {}
        location = (listing.get("location") or "").strip()
        if location:
            places.append(
                {
                    "title": listing.get("title") or "제목 없음",
                    "housingName": listing.get("housing_name") or "",
                    "location": location,
                }
            )

    if not places:
        st.info("지도에 표시할 위치 정보가 없습니다.")
        return

    if not javascript_key or javascript_key.startswith("your-"):
        st.info(
            "지도를 표시하려면 FE_User/.env에 "
            "KAKAO_JAVASCRIPT_KEY를 설정해 주세요."
        )
        return

    places_json = json.dumps(places, ensure_ascii=False).replace("</", "<\\/")
    encoded_key = quote(javascript_key, safe="")

    components.html(
    
    
        f"""
        <!doctype html>
        <html lang="ko">
        <head>
          <meta charset="utf-8">
          <style>
            html, body, #map {{ width: 100%; height: 100%; margin: 0; }}
            #status {{
              position: absolute; z-index: 2; top: 10px; left: 10px;
              padding: 7px 10px; border-radius: 8px;
              background: rgba(255, 255, 255, 0.92); color: #444;
              font: 12px sans-serif; box-shadow: 0 1px 4px rgba(0,0,0,.2);
            }}
            .favorite-star {{
              color: #ffb000; font-size: 34px; line-height: 34px;
              cursor: default; text-shadow: 0 1px 3px rgba(0,0,0,.45);
              transform: translateY(-12px);
            }}
          </style>
        </head>
        <body>
          <div id="map"></div>
          <div id="status">즐겨찾기 위치를 찾는 중...</div>
          <script src="https://dapi.kakao.com/v2/maps/sdk.js?appkey={encoded_key}&libraries=services&autoload=false"></script>
          <script>
            const favoritePlaces = {places_json};
            kakao.maps.load(function() {{
              const mapContainer = document.getElementById('map');
              const mapOption = {{
                center: new kakao.maps.LatLng(37.5665, 126.9780),
                level: 7
              }};
              const map = new kakao.maps.Map(mapContainer, mapOption);
              const geocoder = new kakao.maps.services.Geocoder();
              const bounds = new kakao.maps.LatLngBounds();

              favoritePlaces.forEach((place) => {{
                geocoder.addressSearch(place.location, function(result, status) {{
                  if (status === kakao.maps.services.Status.OK) {{
                    const coords = new kakao.maps.LatLng(result[0].y, result[0].x);
                    const marker = new kakao.maps.Marker({{
                      position: coords,
                      map: map,
                      title: place.title
                    }});

                    const markerEl = document.createElement('div');
                    markerEl.className = 'favorite-star';
                    markerEl.innerHTML = '★';

                    const star = new kakao.maps.CustomOverlay({{
                      position: coords,
                      content: markerEl,
                      map: map
                    }});

                    star.setMap(map);
                    bounds.extend(coords);
                    map.setBounds(bounds);
                  }}
                }});
              }});

              const status = document.getElementById('status');
              if (status) {{
                status.textContent = '즐겨찾기 위치를 표시했습니다.';
              }}
            }});
          </script>
        </body>
        </html>
        """,
        height=560,
    )