"""즐겨찾기 주소의 경도/위도 변환 테스트입니다.

실제 Supabase와 카카오 API에는 연결하지 않습니다.
"""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.favorite_schema import FavoriteWithListing
from app.schemas.listing_schema import ListingPublic
from app.services import favorite_service

client = TestClient(app)


def make_favorite(listing_id: int, location: str) -> FavoriteWithListing:
    return FavoriteWithListing(
        id=listing_id,
        user_id="00000000-0000-0000-0000-000000000001",
        listing_id=listing_id,
        created_at=datetime(2026, 8, 10, 9, 0, 0),
        listing=ListingPublic(
            id=listing_id,
            title=f"테스트 공고 {listing_id}",
            housing_name="테스트하우스",
            area_sqm=Decimal("25.00"),
            recruitment_count=3,
            location=location,
            deposit=10_000_000,
            monthly_rent=200_000,
            application_start_date=date(2026, 8, 1),
            application_end_date=date(2026, 8, 31),
            description="설명",
            source_url="https://example.com",
            created_at=datetime(2026, 8, 1, 9, 0, 0),
        ),
    )


class FavoriteCoordinateServiceTest(unittest.TestCase):
    def test_카카오_x는_경도_y는_위도로_변환한다(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "documents": [{"x": "127.0276", "y": "37.4979"}]
        }

        with patch.object(httpx, "get", return_value=response) as get:
            result = favorite_service.address_to_coordinates("강남구", "rest-key")

        self.assertEqual(result, (127.0276, 37.4979))
        self.assertEqual(get.call_args.kwargs["params"]["query"], "서울특별시 강남구")
        self.assertEqual(
            get.call_args.kwargs["headers"]["Authorization"],
            "KakaoAK rest-key",
        )

    def test_검색_결과가_없으면_none을_반환한다(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"documents": []}
        with patch.object(httpx, "get", return_value=response):
            self.assertIsNone(
                favorite_service.address_to_coordinates("없는 주소", "rest-key")
            )

    def test_좌표가_없는_비정상_응답은_명확한_오류로_바꾼다(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"documents": [{"address_name": "서울"}]}
        with patch.object(httpx, "get", return_value=response):
            with self.assertRaisesRegex(
                favorite_service.KakaoGeocodingError,
                "좌표가 없습니다",
            ):
                favorite_service.address_to_coordinates("서울", "rest-key")

    def test_같은_주소는_한_번만_변환한다(self):
        favorites = [make_favorite(1, "강남구"), make_favorite(2, "강남구")]
        with patch.object(
            favorite_service, "favorite_get_mypage", return_value=favorites
        ), patch.object(
            favorite_service, "get_kakao_rest_api_key", return_value="rest-key"
        ), patch.object(
            favorite_service,
            "address_to_coordinates",
            return_value=(127.0276, 37.4979),
        ) as geocode:
            result = favorite_service.favorite_get_coordinates("user-id")

        geocode.assert_called_once_with("강남구", "rest-key")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].longitude, 127.0276)
        self.assertEqual(result[0].latitude, 37.4979)


class FavoriteCoordinateApiTest(unittest.TestCase):
    def test_좌표_변환_응답을_반환한다(self):
        converted = [
            {
                "listing_id": 1,
                "title": "테스트 공고",
                "location": "강남구",
                "longitude": 127.0276,
                "latitude": 37.4979,
            }
        ]
        with patch(
            "app.routers.favorite_router.favorite_get_coordinates",
            return_value=converted,
        ):
            response = client.get("/favorites/mypage/user-id/coordinates")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"][0]
        self.assertEqual(data["longitude"], 127.0276)
        self.assertEqual(data["latitude"], 37.4979)

    def test_카카오_api_오류는_502로_응답한다(self):
        with patch(
            "app.routers.favorite_router.favorite_get_coordinates",
            side_effect=favorite_service.KakaoGeocodingError("키 오류"),
        ):
            response = client.get("/favorites/mypage/user-id/coordinates")

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["message"], "키 오류")


if __name__ == "__main__":
    unittest.main()
