"""실제 app/main.py 구조에 AI 상담 라우터만 추가한 통합 테스트 서버입니다.

기존 app/main.py는 수정하지 않습니다. 이 파일은 8010 포트에서 기존 API와
AI 상담 API가 함께 동작하는지 확인할 때 사용합니다.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.log_store import start_simulator_thread
from app.exceptions.handlers import register_exception_handlers
from app.routers.admin_router import admin_router
from app.routers.chat_router import chat_router
from app.routers.favorite_router import favorite_router
from app.routers.listing_router import listing_router
from app.routers.log_router import log_router
from app.routers.profile_router import profile_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 실제 앱과 같은 시작 흐름을 사용해 기존 기능과의 충돌도 함께 확인합니다.
    start_simulator_thread()
    yield


tags_metadata = [
    {
        "name": "Admin",
        "description": "관리자 로그인, 청약정보 등록/삭제, 즐겨찾기 현황 조회",
    },
    {
        "name": "Profile",
        "description": "mypage 프로필 조회/수정",
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
        "description": "실시간 로그 대시보드용 조회 API",
    },
    {
        "name": "Chat",
        "description": "로그인 사용자의 Gemini 상담, 요약 저장 및 조회",
    },
]

app = FastAPI(
    title="공공임대 청약 통합 안내 서비스 - AI 통합 테스트",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

register_exception_handlers(app)

# 실제 main.py에 등록된 기존 라우터입니다.
app.include_router(admin_router)
app.include_router(profile_router)
app.include_router(listing_router)
app.include_router(favorite_router)
app.include_router(log_router)

# 통합 테스트에서만 추가한 AI 상담 라우터입니다.
app.include_router(chat_router)
