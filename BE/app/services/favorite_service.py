# favorite_service.py
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from app.core.supabase_config import get_supabase
from app.schemas.favorite_schema import (
    FavoriteCoordinate,
    FavoriteCreate,
    FavoriteDetail,
    FavoritePublic,
    FavoriteRanking,
    FavoriteWithListing,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"
KAKAO_ADDRESS_SEARCH_URL = "https://dapi.kakao.com/v2/local/search/address.json"
KAKAO_REQUEST_TIMEOUT = 10.0


class KakaoGeocodingError(Exception):
    """카카오 주소 검색 API 호출 자체가 실패했을 때 사용합니다."""


def get_kakao_rest_api_key() -> str:
    """BE/.env에서 카카오 REST API 키를 읽습니다."""

    load_dotenv(ENV_PATH)
    value = os.getenv("KAKAO_REST_API_KEY", "").strip()
    if not value:
        raise KakaoGeocodingError(
            f"KAKAO_REST_API_KEY 값이 없습니다. {ENV_PATH} 파일을 확인하세요."
        )
    if value.startswith("your-"):
        raise KakaoGeocodingError("KAKAO_REST_API_KEY 값이 예시 값입니다.")
    return value


def address_to_coordinates(
    address: str,
    rest_api_key: str,
) -> tuple[float, float] | None:
    """주소를 WGS84 경도, 위도 순서로 변환합니다."""

    query = address.strip()
    if not query:
        return None

    # 현재 DB에는 '강남구'처럼 서울 자치구만 저장될 수 있어 검색 범위를 보완합니다.
    if not query.startswith(("서울", "서울특별시")):
        query = f"서울특별시 {query}"

    try:
        response = httpx.get(
            KAKAO_ADDRESS_SEARCH_URL,
            headers={"Authorization": f"KakaoAK {rest_api_key}"},
            params={"query": query, "analyze_type": "similar", "size": 1},
            timeout=KAKAO_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as error:
        if error.response.status_code in (401, 403):
            message = "카카오 REST API 키가 올바르지 않거나 사용할 권한이 없습니다."
        else:
            message = f"카카오 주소 검색 API가 {error.response.status_code} 오류를 반환했습니다."
        raise KakaoGeocodingError(message) from error
    except httpx.RequestError as error:
        raise KakaoGeocodingError("카카오 주소 검색 API에 연결할 수 없습니다.") from error

    try:
        documents = response.json().get("documents") or []
    except (ValueError, AttributeError) as error:
        raise KakaoGeocodingError("카카오 주소 검색 API 응답 형식이 올바르지 않습니다.") from error

    if not documents:
        return None

    try:
        first = documents[0]
        return float(first["x"]), float(first["y"])
    except (KeyError, TypeError, ValueError) as error:
        raise KakaoGeocodingError("카카오 주소 검색 결과에 좌표가 없습니다.") from error


def favorite_get_coordinates(user_id: str) -> list[FavoriteCoordinate]:
    """사용자의 즐겨찾기 주소를 경도와 위도로 변환해 반환합니다.

    좌표는 응답에만 포함하며 Supabase에는 저장하지 않습니다. 같은 주소는 한 요청에서
    한 번만 변환해 외부 API 호출을 줄입니다.
    """

    favorites = favorite_get_mypage(user_id)
    if not favorites:
        return []

    rest_api_key = get_kakao_rest_api_key()
    coordinate_by_location: dict[str, tuple[float, float] | None] = {}
    results: list[FavoriteCoordinate] = []

    for favorite in favorites:
        location = favorite.listing.location.strip()
        if location not in coordinate_by_location:
            coordinate_by_location[location] = address_to_coordinates(
                location,
                rest_api_key,
            )

        coordinates = coordinate_by_location[location]
        longitude, latitude = coordinates if coordinates is not None else (None, None)
        results.append(
            FavoriteCoordinate(
                listing_id=favorite.listing_id,
                title=favorite.listing.title,
                location=location,
                longitude=longitude,
                latitude=latitude,
            )
        )

    return results


def favorite_create(favorite: FavoriteCreate) -> FavoritePublic | None:
    supabase = get_supabase()
    result = (
        supabase.table("favorites")
        .insert(
            {
                "user_id": favorite.user_id,
                "listing_id": favorite.listing_id,
            }
        )
        .execute()
    )
    if not result.data:
        return None
    return FavoritePublic.model_validate(result.data[0])


def favorite_get_by_user_and_listing(user_id: str, listing_id: int) -> FavoritePublic | None:
    supabase = get_supabase()
    result = (
        supabase.table("favorites")
        .select("*")
        .eq("user_id", user_id)
        .eq("listing_id", listing_id)
        .execute()
    )
    if not result.data:
        return None
    return FavoritePublic.model_validate(result.data[0])


def favorite_get_mypage(user_id: str) -> list[FavoriteWithListing]:
    """ mypage에서 내가 즐겨찾기한 청약정보 목록을 조회합니다. """
    supabase = get_supabase()
    result = (
        supabase.table("favorites")
        .select("*, listing:listings(*)")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [FavoriteWithListing.model_validate(item) for item in result.data]


def favorite_delete(user_id: str, listing_id: int) -> FavoritePublic | None:
    supabase = get_supabase()
    result = (
        supabase.table("favorites")
        .delete()
        .eq("user_id", user_id)
        .eq("listing_id", listing_id)
        .execute()
    )
    if not result.data:
        return None
    return FavoritePublic.model_validate(result.data[0])


def favorite_ranking() -> list[FavoriteRanking]:
    """ 관리자용: 즐겨찾기가 많은 청약정보 순으로 조회합니다. """
    supabase = get_supabase()
    result = (
        supabase.table("favorites")
        .select("listing_id, listings(title)")
        .execute()
    )

    counts: dict[int, dict] = {}
    for row in result.data:
        listing_id = row["listing_id"]
        listing = row.get("listings") or {}
        if listing_id not in counts:
            counts[listing_id] = {
                "listing_id": listing_id,
                "title": listing.get("title", ""),
                "favorite_count": 0,
            }
        counts[listing_id]["favorite_count"] += 1

    ranking = sorted(counts.values(), key=lambda item: item["favorite_count"], reverse=True)
    return [FavoriteRanking.model_validate(item) for item in ranking]


def favorite_detail(listing_id: int | None) -> list[FavoriteDetail]:
    """ 관리자용: 어떤 유저가 어떤 청약정보를 즐겨찾기했는지 조회합니다.

    favorites.user_id는 auth.users를 참조하고 profiles를 참조하지 않아 PostgREST가
    favorites-profiles 관계를 자동으로 찾지 못합니다. 그래서 nickname은 user_id로
    profiles를 따로 조회해 채웁니다.
    """
    supabase = get_supabase()
    query = (
        supabase.table("favorites")
        .select("id, user_id, listing_id, created_at, listings(title)")
    )
    if listing_id is not None:
        query = query.eq("listing_id", listing_id)

    result = query.order("created_at", desc=True).execute()

    user_ids = list({row["user_id"] for row in result.data})
    nickname_by_user_id: dict[str, str | None] = {}
    if user_ids:
        profiles_result = (
            supabase.table("profiles")
            .select("id, nickname")
            .in_("id", user_ids)
            .execute()
        )
        nickname_by_user_id = {row["id"]: row.get("nickname") for row in profiles_result.data}

    details = []
    for row in result.data:
        listing = row.get("listings") or {}
        details.append(
            FavoriteDetail(
                favorite_id=row["id"],
                user_id=row["user_id"],
                nickname=nickname_by_user_id.get(row["user_id"]),
                listing_id=row["listing_id"],
                title=listing.get("title", ""),
                created_at=row["created_at"],
            )
        )
    return details
