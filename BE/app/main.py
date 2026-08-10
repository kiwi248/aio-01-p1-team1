import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.log_store import start_simulator_thread
from app.exceptions.handlers import register_exception_handlers
from app.routers.admin_router import admin_router
from app.routers.favorite_router import favorite_router
from app.routers.listing_router import listing_router
from app.routers.log_router import log_router
from app.routers.profile_router import profile_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버가 시작될 때 로그 시뮬레이터를 백그라운드 스레드로 한 번만 띄웁니다.
    start_simulator_thread()
    yield


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
        "name": "Favorite",
        "description": "mypage 즐겨찾기 등록/조회/삭제",
    },
    {
        "name": "Log",
        "description": "실시간 로그 대시보드용 조회 API (메모리 buffer, DB 미사용)",
    },
]

app = FastAPI(
    title="공공임대 청약 통합 안내 서비스",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

# Streamlit Cloud(FE_Admin, FE_User)는 백엔드와 다른 도메인에서 API를 호출하므로
# CORS를 허용해야 합니다. ALLOWED_ORIGINS는 쉼표로 구분된 도메인 목록이며,
# 아직 배포 주소를 모르는 개발 단계에서는 기본값 "*"(전체 허용)를 씁니다.
# 쿠키/세션 인증을 쓰지 않는 API라 "*"를 써도 자격 증명이 새는 위험은 없습니다.
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(admin_router)
app.include_router(profile_router)
app.include_router(listing_router)
app.include_router(favorite_router)
app.include_router(log_router)
