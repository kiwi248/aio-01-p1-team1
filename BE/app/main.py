from fastapi import FastAPI

from app.exceptions.handlers import register_exception_handlers
from app.routers.admin_router import admin_router
from app.routers.favorite_router import favorite_router
from app.routers.listing_router import listing_router
from app.routers.location_router import location_router
from app.routers.profile_router import profile_router

# Swagger 문서(/docs)에 표시할 API 그룹 설명입니다.
tags_metadata = [
    {
        "name": "Admin",
        "description": "관리자 로그인, 청약정보 등록/삭제, 즐겨찾기 현황 조회",
    },
    {
        "name": "Profile",
        "description": "mypage 프로필(닉네임) 조회/수정. 회원가입·로그인은 Supabase Auth가 처리합니다.",
    },
    {
        "name": "Listing",
        "description": "청약정보 조회 및 조건검색",
    },
    {
        "name": "Location",
        "description": "주소 좌표 변환 및 주변 생활시설 조회",
    },
    {
        "name": "Favorite",
        "description": "mypage 즐겨찾기 등록/조회/삭제",
    },
]

app = FastAPI(title="공공임대 청약 통합 안내 서비스", openapi_tags=tags_metadata)

register_exception_handlers(app)

app.include_router(admin_router)
app.include_router(profile_router)
app.include_router(listing_router)
app.include_router(location_router)
app.include_router(favorite_router)
