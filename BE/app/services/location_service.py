import os
from pathlib import Path

import httpx
from fastapi import HTTPException
from dotenv import load_dotenv

from app.schemas.location_schema import GeocodeResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

KAKAO_ADDRESS_SEARCH_URL = (
    "https://dapi.kakao.com/v2/local/search/address.json"
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


def geocode_address(address: str) -> GeocodeResult:
    """입력받은 주소를 위도와 경도로 변환합니다."""

    address = address.strip()

    if not address:
        raise HTTPException(
            status_code=400,
            detail="주소를 입력해 주세요.",
        )

    headers = {
        "Authorization": f"KakaoAK {get_kakao_api_key()}",
    }
    params = {
        "query": address,
    }

    try:
        response = httpx.get(
            KAKAO_ADDRESS_SEARCH_URL,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=504,
            detail="주소 검색 응답 시간이 초과되었습니다.",
        ) from error
    except httpx.RequestError as error:
        raise HTTPException(
            status_code=502,
            detail="주소 검색 서버에 연결할 수 없습니다.",
        ) from error

    if response.status_code in (401, 403):
        raise HTTPException(
            status_code=500,
            detail="Kakao API 설정을 확인해 주세요.",
        )

    if response.is_error:
        raise HTTPException(
            status_code=502,
            detail="주소 검색 중 외부 API 오류가 발생했습니다.",
        )

    try:
        payload = response.json()
    except ValueError as error:
        raise HTTPException(
            status_code=502,
            detail="주소 검색 서버가 올바른 응답을 반환하지 않았습니다.",
        ) from error

    documents = payload.get("documents") or []

    if not documents:
        raise HTTPException(
            status_code=404,
            detail="입력한 주소를 찾을 수 없습니다.",
        )

    document = documents[0]

    road_address = document.get("road_address") or {}
    basic_address = document.get("address") or {}

    normalized_address = (
        road_address.get("address_name")
        or basic_address.get("address_name")
        or document.get("address_name")
        or address
    )

    try:
        return GeocodeResult(
            address=normalized_address,
            latitude=float(document["y"]),
            longitude=float(document["x"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="주소 검색 결과에서 좌표를 확인할 수 없습니다.",
        ) from error