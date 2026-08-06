# listing_router.py
from fastapi import APIRouter, HTTPException, Query

from app.core.api_response import ApiResponse
from app.services.listing_service import listing_get, listing_get_all, listing_search

listing_router = APIRouter(prefix="/listings", tags=["Listing"])

# 200: 정상 - 정상 실행 되면 자동 전송
# 404: 데이터 없음

# 1. 전체 조회
@listing_router.get("/getall")
def get_all() -> ApiResponse:
    listings = listing_get_all()
    return ApiResponse(
        success=True,
        message="청약정보 목록을 조회했습니다.",
        data=listings,
    )


# 2. 조건검색 (최신순, 대상, 위치, 금액, 자격조건)
@listing_router.get("/search")
def search(
    type: str | None = Query(default=None),
    location: str | None = Query(default=None),
    min_price: int | None = Query(default=None, ge=0),
    max_price: int | None = Query(default=None, ge=0),
    eligibility: str | None = Query(default=None),
) -> ApiResponse:
    listings = listing_search(
        type=type,
        location=location,
        min_price=min_price,
        max_price=max_price,
        eligibility=eligibility,
    )
    return ApiResponse(
        success=True,
        message="청약정보 검색에 성공했습니다.",
        data=listings,
    )


# 3. 한개 조회
@listing_router.get("/get/{listing_id}")
def get(listing_id: int) -> ApiResponse:
    listing = listing_get(listing_id)
    if listing is None:
        raise HTTPException(status_code=404, detail=f"청약정보 ID {listing_id}를 찾을 수 없습니다.")
    return ApiResponse(
        success=True,
        message="청약정보를 조회했습니다.",
        data=listing,
    )
