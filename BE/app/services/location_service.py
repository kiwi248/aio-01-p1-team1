import math
import os
from pathlib import Path
from typing import Any, Literal

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

from app.schemas.location_schema import GeocodeResult, NearbyStation


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

KAKAO_ADDRESS_SEARCH_URL = (
    "https://dapi.kakao.com/v2/local/search/address.json"
)
KAKAO_KEYWORD_SEARCH_URL = (
    "https://dapi.kakao.com/v2/local/search/keyword.json"
)
KAKAO_CATEGORY_SEARCH_URL = (
    "https://dapi.kakao.com/v2/local/search/category.json"
)
REQUEST_TIMEOUT = 10.0


def get_kakao_api_key() -> str:
    """환경변수에서 Kakao REST API 키를 읽습니다."""

    load_dotenv(ENV_PATH)

    api_key = os.getenv("KAKAO_REST_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Kakao REST API 키가 설정되지 않았습니다.",
        )

    return api_key


def request_kakao(
    url: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Kakao 위치 API에 요청하고 JSON 응답을 반환합니다."""

    headers = {
        "Authorization": f"KakaoAK {get_kakao_api_key()}",
    }

    try:
        response = httpx.get(
            url,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=504,
            detail="위치 검색 응답 시간이 초과되었습니다.",
        ) from error
    except httpx.RequestError as error:
        raise HTTPException(
            status_code=502,
            detail="위치 검색 서버에 연결할 수 없습니다.",
        ) from error

    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=500,
            detail="Kakao API 설정을 확인해 주세요.",
        )

    if response.is_error:
        raise HTTPException(
            status_code=502,
            detail="위치 검색 중 외부 API 오류가 발생했습니다.",
        )

    try:
        payload = response.json()
    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail="위치 검색 서버가 올바른 응답을 반환하지 않았습니다.",
        ) from error

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=502,
            detail="위치 검색 응답 형식이 올바르지 않습니다.",
        )

    return payload


def make_geocode_result(
    document: dict[str, Any],
    original_query: str,
    matched_by: Literal["address", "keyword"],
) -> GeocodeResult:
    """Kakao 검색 결과 한 건을 공통 좌표 모델로 변환합니다."""

    if matched_by == "address":
        road_address = document.get("road_address") or {}
        basic_address = document.get("address") or {}

        normalized_address = (
            road_address.get("address_name")
            or basic_address.get("address_name")
            or document.get("address_name")
            or original_query
        )
    else:
        normalized_address = (
            document.get("road_address_name")
            or document.get("address_name")
            or document.get("place_name")
            or original_query
        )

    try:
        return GeocodeResult(
            address=normalized_address,
            latitude=float(document["y"]),
            longitude=float(document["x"]),
            matched_by=matched_by,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="위치 검색 결과에서 좌표를 확인할 수 없습니다.",
        ) from error


def geocode_address(address: str) -> GeocodeResult:
    """주소를 먼저 검색하고, 실패하면 장소명으로 검색합니다."""

    address = address.strip()

    if not address:
        raise HTTPException(
            status_code=400,
            detail="주소 또는 장소명을 입력해 주세요.",
        )

    address_payload = request_kakao(
        KAKAO_ADDRESS_SEARCH_URL,
        params={"query": address},
    )
    address_documents = address_payload.get("documents") or []

    if address_documents:
        return make_geocode_result(
            document=address_documents[0],
            original_query=address,
            matched_by="address",
        )

    keyword_payload = request_kakao(
        KAKAO_KEYWORD_SEARCH_URL,
        params={
            "query": address,
            "size": 1,
        },
    )
    keyword_documents = keyword_payload.get("documents") or []

    if keyword_documents:
        return make_geocode_result(
            document=keyword_documents[0],
            original_query=address,
            matched_by="keyword",
        )

    raise HTTPException(
        status_code=404,
        detail=(
            "입력한 주소 또는 장소를 찾을 수 없습니다. "
            "도로명 주소, 건물명 또는 아파트명을 확인해 주세요."
        ),
    )


def estimate_walking_minutes(distance_m: int) -> int:
    """직선거리를 보정해 대략적인 도보시간을 계산합니다."""

    route_factor = 1.25
    walking_speed_m_per_minute = 75

    estimated_route_distance = distance_m * route_factor
    estimated_minutes = math.ceil(
        estimated_route_distance / walking_speed_m_per_minute
    )

    return max(1, estimated_minutes)


def find_nearby_subway_stations(
    latitude: float,
    longitude: float,
    radius_m: int = 2000,
    limit: int = 3,
) -> list[NearbyStation]:
    """주어진 좌표 반경 내 가까운 지하철역을 검색합니다."""

    if not -90 <= latitude <= 90:
        raise HTTPException(
            status_code=400,
            detail="위도 값이 올바르지 않습니다.",
        )

    if not -180 <= longitude <= 180:
        raise HTTPException(
            status_code=400,
            detail="경도 값이 올바르지 않습니다.",
        )

    if not 100 <= radius_m <= 20000:
        raise HTTPException(
            status_code=400,
            detail="검색 반경은 100m 이상 20km 이하여야 합니다.",
        )

    if not 1 <= limit <= 15:
        raise HTTPException(
            status_code=400,
            detail="조회 개수는 1개 이상 15개 이하여야 합니다.",
        )

    payload = request_kakao(
        KAKAO_CATEGORY_SEARCH_URL,
        params={
            "category_group_code": "SW8",
            "x": longitude,
            "y": latitude,
            "radius": radius_m,
            "sort": "distance",
            "size": limit,
        },
    )

    documents = payload.get("documents") or []
    stations: list[NearbyStation] = []

    for document in documents:
        try:
            distance_m = int(document.get("distance") or 0)

            station = NearbyStation(
                name=document["place_name"],
                address=(
                    document.get("road_address_name")
                    or document.get("address_name")
                    or ""
                ),
                latitude=float(document["y"]),
                longitude=float(document["x"]),
                distance_m=distance_m,
                estimated_walking_minutes=estimate_walking_minutes(
                    distance_m
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise HTTPException(
                status_code=502,
                detail="지하철역 검색 결과 형식이 올바르지 않습니다.",
            ) from error

        stations.append(station)

    return stations