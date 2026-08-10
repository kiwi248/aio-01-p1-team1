"""기존 app/main.py 없이 독립 FastAPI 앱으로 확인하는 챗봇 라우터 테스트입니다."""

import os
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.auth_dependency import AuthenticatedUser, get_current_user
from app.exceptions.handlers import register_exception_handlers
from app.routers.chat_router import chat_router
from app.services import chat_service


def fake_current_user() -> AuthenticatedUser:
    return AuthenticatedUser(id="test-user", email="test@example.com")


test_app = FastAPI()
register_exception_handlers(test_app)
test_app.include_router(chat_router)
test_app.dependency_overrides[get_current_user] = fake_current_user
client = TestClient(test_app)


class ChatRouterTest(unittest.TestCase):
    def setUp(self):
        chat_service._preview_summaries.clear()

    def test_mock_채팅_응답(self):
        payload = {
            "question": "두 번째 질문",
            "messages": [
                {"role": "user", "content": "첫 질문"},
                {"role": "assistant", "content": "첫 답변"},
            ],
        }

        with patch.dict(os.environ, {"CHAT_GEMINI_MODE": "mock"}, clear=False):
            response = client.post("/chat/message", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["data"]["history_count"], 2)

    def test_빈_질문은_검증_오류(self):
        response = client.post("/chat/message", json={"question": "   ", "messages": []})

        self.assertEqual(response.status_code, 422)
        self.assertFalse(response.json()["success"])

    def test_요약_저장_후_목록에서_조회한다(self):
        payload = {
            "messages": [
                {"role": "user", "content": "청약이 무엇인가요?"},
                {"role": "assistant", "content": "청약 기본 설명입니다."},
            ]
        }

        with patch.dict(
            os.environ,
            {"CHAT_GEMINI_MODE": "mock", "CHAT_SUMMARY_STORAGE": "preview"},
            clear=False,
        ):
            save_response = client.post("/chat/save", json=payload)
            list_response = client.get("/chat/summaries")

        self.assertEqual(save_response.status_code, 200)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["data"]), 1)
        self.assertEqual(list_response.json()["data"][0]["user_id"], "test-user")

    def test_메시지_한_개는_저장할_수_없다(self):
        response = client.post(
            "/chat/save",
            json={"messages": [{"role": "user", "content": "답변이 없는 질문"}]},
        )

        self.assertEqual(response.status_code, 422)


class ChatRouterAuthenticationTest(unittest.TestCase):
    def test_인증_없는_요청은_거절한다(self):
        app = FastAPI()
        register_exception_handlers(app)
        app.include_router(chat_router)
        unauthenticated_client = TestClient(app)

        response = unauthenticated_client.post(
            "/chat/message",
            json={"question": "질문", "messages": []},
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(response.json()["success"])


if __name__ == "__main__":
    unittest.main()
