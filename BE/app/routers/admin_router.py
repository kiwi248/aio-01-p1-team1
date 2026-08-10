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
    listing_clear_image,
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
    detail_address: Annotated[str | None, Form(max_length=255)] = None,
    image: Annotated[UploadFile | None, File()] = None,
    remove_image: Annotated[bool, Form()] = False,
) -> ApiResponse:
    current_listing = listing_get(listing_id)
    if current_listing is None:
        raise HTTPException(status_code=404, detail="청약정보를 찾을 수 없습니다.")

    # 상세주소를 비워서 보내면 빈 문자열 대신 값 없음으로 저장합니다.
    detail_address = (detail_address or "").strip() or None

    has_new_image = image is not None and bool(image.filename)

    # 새로 올리면서 동시에 지우라는 요청은 뜻이 서로 어긋나므로 받지 않습니다.
    if has_new_image and remove_image:
        raise HTTPException(
            status_code=400,
            detail="새 이미지 업로드와 기존 이미지 삭제를 함께 선택할 수 없습니다.",
        )

    # 이미지는 세 가지 중 하나입니다.
    #   새 파일이 오면        -> 교체
    #   지우라고 하면         -> 이미지 없음(None)
    #   둘 다 아니면          -> 기존 이미지 유지
    image_url = current_listing.image_url
    if has_new_image:
        image_url = await upload_listing_image(image)
    elif remove_image:
        image_url = None

    listing = ListingCreate(
        title=title,
        housing_name=housing_name,
        area_sqm=area_sqm,
        recruitment_count=recruitment_count,
        location=location,
        detail_address=detail_address,
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
        # 기존 이미지는 아직 공고가 쓰고 있으므로 건드리지 않습니다.
        if has_new_image:
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


# 4-1. 청약정보 이미지만 삭제
@admin_router.delete("/listings/{listing_id}/image")
def remove_listing_image(listing_id: int) -> ApiResponse:
    """공고는 그대로 두고 이미지만 지웁니다.

    수정 API와 따로 둔 이유는, 관리자가 화면에 입력만 해 두고 아직 저장하지 않은
    제목·금액 같은 값이 이미지를 지울 때 함께 저장되지 않도록 하기 위해서입니다.
    이 API는 공고 id만 받고 다른 값은 받지 않습니다.
    """

    current_listing = listing_get(listing_id)
    if current_listing is None:
        raise HTTPException(status_code=404, detail="청약정보를 찾을 수 없습니다.")

    # 이미 이미지가 없으면 지울 것이 없습니다. 여러 번 눌러도 여기서 끝납니다.
    if not current_listing.image_url:
        return ApiResponse(
            success=True,
            message="이미 이미지가 없는 청약정보입니다.",
            data=current_listing,
        )

    updated_listing = listing_clear_image(listing_id)
    if updated_listing is None:
        # DB가 아직 기존 이미지를 가리키고 있으므로 파일을 지우면 공고가 깨집니다.
        raise HTTPException(status_code=500, detail="이미지 삭제에 실패했습니다.")

    # DB에서 참조를 지운 뒤에만 파일을 지웁니다.
    # 외부 URL·공유 이미지 제외와 실패 기록은 image_service가 맡습니다.
    delete_listing_image(current_listing.image_url)

    return ApiResponse(
        success=True,
        message="이미지를 삭제했습니다.",
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
