# admin_router.py
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.core.api_response import ApiResponse
from app.schemas.admin_schema import AdminLogin
from app.schemas.listing_schema import ListingCreate
from app.services.admin_service import admin_login_process
from app.services.favorite_service import favorite_detail, favorite_ranking
from app.services.image_service import delete_listing_image, upload_listing_image
from app.services.listing_service import listing_create, listing_delete, listing_get

admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# 200: 정상 - 정상 실행 되면 자동 전송
# 401: 로그인 실패
# 404: 데이터 없음
# 500: 서버 또는 DB 처리 실패

# 1. 관리자 로그인
@admin_router.post("/login")
def login(admin: AdminLogin) -> ApiResponse:
    logged_in_admin = admin_login_process(admin)
    return ApiResponse(
        success=True,
        message="관리자 로그인에 성공했습니다.",
        data=logged_in_admin,
    )


# 2. 청약정보 등록
@admin_router.post("/listings/create")
def create_listing(listing: ListingCreate) -> ApiResponse:
    created_listing = listing_create(listing)
    if created_listing is None:
        raise HTTPException(status_code=500, detail="청약정보 등록에 실패했습니다.")
    return ApiResponse(
        success=True,
        message="청약정보가 등록되었습니다.",
        data=created_listing,
    )


# 3. 청약정보 이미지 업로드
@admin_router.post("/listings/images")
async def create_listing_image(
    image: Annotated[UploadFile, File()],
) -> ApiResponse:
    image_url = await upload_listing_image(image)
    return ApiResponse(
        success=True,
        message="이미지를 업로드했습니다.",
        data={"image_url": image_url},
    )


# 4. 청약정보 삭제
@admin_router.delete("/listings/delete/{listing_id}")
def delete_listing(listing_id: int) -> ApiResponse:
    current_listing = listing_get(listing_id)
    if current_listing is None:
        raise HTTPException(status_code=404, detail="청약정보를 찾을 수 없습니다.")

    deleted_listing = listing_delete(listing_id)
    if deleted_listing is None:
        raise HTTPException(status_code=500, detail="청약정보 삭제에 실패했습니다.")

    # 공고를 지운 뒤 Storage에 남은 이미지 파일도 함께 지웁니다.
    delete_listing_image(current_listing.image_url)

    return ApiResponse(
        success=True,
        message="청약정보가 삭제되었습니다.",
        data=deleted_listing,
    )


# 5. 즐겨찾기 많은 순 조회
@admin_router.get("/favorites/ranking")
def get_favorite_ranking() -> ApiResponse:
    ranking = favorite_ranking()
    return ApiResponse(
        success=True,
        message="즐겨찾기 순위를 조회했습니다.",
        data=ranking,
    )


# 6. 어떤 유저가 어떤 청약정보를 즐겨찾기했는지 조회
@admin_router.get("/favorites/detail")
def get_favorite_detail(listing_id: int | None = Query(default=None)) -> ApiResponse:
    details = favorite_detail(listing_id)
    return ApiResponse(
        success=True,
        message="즐겨찾기 상세 내역을 조회했습니다.",
        data=details,
    )
