# admin_router.py
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.core.api_response import ApiResponse
from app.schemas.admin_schema import AdminLogin
from app.schemas.listing_schema import ListingCreate
from app.services.admin_service import admin_login_process
from app.services.favorite_service import favorite_detail, favorite_ranking
from app.services.image_service import delete_listing_image, upload_listing_image
from app.services.listing_service import (
    listing_create,
    listing_delete,
    listing_get,
    listing_update,
)

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


# 4. 청약정보 수정
@admin_router.put("/listings/update/{listing_id}")
async def update_listing(
    listing_id: int,
    title: Annotated[str, Form(min_length=1, max_length=255)],
    housing_name: Annotated[str, Form(min_length=1, max_length=255)],
    area_sqm: Annotated[Decimal, Form(gt=0)],
    recruitment_count: Annotated[int, Form(gt=0)],
    location: Annotated[str, Form(min_length=1, max_length=50)],
    deposit: Annotated[int, Form(ge=0)],
    monthly_rent: Annotated[int, Form(ge=0)],
    application_start_date: Annotated[date, Form()],
    application_end_date: Annotated[date, Form()],
    description: Annotated[str, Form(min_length=1)],
    source_url: Annotated[str, Form(min_length=1)],
    image: Annotated[UploadFile | None, File()] = None,
) -> ApiResponse:
    current_listing = listing_get(listing_id)
    if current_listing is None:
        raise HTTPException(status_code=404, detail="청약정보를 찾을 수 없습니다.")

    # 새 이미지를 고르지 않으면 기존 이미지를 그대로 씁니다.
    image_url = current_listing.image_url
    if image is not None and image.filename:
        image_url = await upload_listing_image(image)

    listing = ListingCreate(
        title=title,
        housing_name=housing_name,
        area_sqm=area_sqm,
        recruitment_count=recruitment_count,
        location=location,
        deposit=deposit,
        monthly_rent=monthly_rent,
        application_start_date=application_start_date,
        application_end_date=application_end_date,
        description=description,
        image_url=image_url,
        source_url=source_url,
    )
    updated_listing = listing_update(listing_id, listing)

    if updated_listing is None:
        # DB 수정이 실패했는데 새 이미지를 이미 올렸다면, 쓰이지 않는 파일이 되므로 지웁니다.
        if image_url != current_listing.image_url:
            delete_listing_image(image_url)
        raise HTTPException(status_code=500, detail="청약정보 수정에 실패했습니다.")

    # DB 수정이 끝난 뒤에만 예전 이미지를 지웁니다.
    if image_url != current_listing.image_url:
        delete_listing_image(current_listing.image_url)

    return ApiResponse(
        success=True,
        message="청약정보가 수정되었습니다.",
        data=updated_listing,
    )


# 5. 청약정보 삭제
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


# 6. 즐겨찾기 많은 순 조회
@admin_router.get("/favorites/ranking")
def get_favorite_ranking() -> ApiResponse:
    ranking = favorite_ranking()
    return ApiResponse(
        success=True,
        message="즐겨찾기 순위를 조회했습니다.",
        data=ranking,
    )


# 7. 어떤 유저가 어떤 청약정보를 즐겨찾기했는지 조회
@admin_router.get("/favorites/detail")
def get_favorite_detail(listing_id: int | None = Query(default=None)) -> ApiResponse:
    details = favorite_detail(listing_id)
    return ApiResponse(
        success=True,
        message="즐겨찾기 상세 내역을 조회했습니다.",
        data=details,
    )
