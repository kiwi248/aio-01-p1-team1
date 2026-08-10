"""독립 실행과 최종 앱에서 함께 사용할 AI 상담 API입니다."""

from fastapi import APIRouter, Depends

from app.core.api_response import ApiResponse
from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.schemas.chat_schema import ChatRequest, ChatSaveRequest
from app.services.chat_service import (
    create_chat_answer,
    create_chat_summary,
    get_chat_profile,
    get_summary_storage_mode,
    list_chat_summaries,
)


chat_router = APIRouter(prefix="/chat", tags=["Chat"])


@chat_router.get("/health")
def health() -> ApiResponse:
    return ApiResponse(
        success=True,
        message="AI 상담 테스트 API가 실행 중입니다.",
        data={"summary_storage": get_summary_storage_mode()},
    )


@chat_router.get("/me")
def me(user: AuthenticatedUser = Depends(get_current_user)) -> ApiResponse:
    return ApiResponse(
        success=True,
        message="상담 사용자 정보를 조회했습니다.",
        data=get_chat_profile(user.id, user.email),
    )


@chat_router.post("/message")
def message(
    request: ChatRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse:
    answer = create_chat_answer(request.messages, request.question)
    return ApiResponse(success=True, message="AI 상담 답변을 생성했습니다.", data=answer)


@chat_router.post("/save")
def save(
    request: ChatSaveRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse:
    summary = create_chat_summary(user.id, request.messages)
    return ApiResponse(success=True, message="상담 요약 미리보기를 저장했습니다.", data=summary)


@chat_router.get("/summaries")
def summaries(user: AuthenticatedUser = Depends(get_current_user)) -> ApiResponse:
    items = list_chat_summaries(user.id)
    return ApiResponse(success=True, message="저장된 상담 요약을 조회했습니다.", data=items)
