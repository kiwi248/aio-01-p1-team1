# test_create_form.py
"""청약정보 등록 폼 입력값 초기화 테스트.

Streamlit이나 서버에 연결하지 않는 순수 함수만 확인합니다.
FE_Admin 폴더에서 아래 명령으로 실행합니다.

    python -m unittest discover -s tests
"""

import unittest

from core.create_form import CREATE_FORM_KEYS, reset_form_state


def filled_state() -> dict:
    """등록 폼에 값이 들어 있는 상태를 흉내 냅니다."""
    return {key: f"{key} 값" for key in CREATE_FORM_KEYS}


class CreateFormKeysTest(unittest.TestCase):
    def test_등록_폼_입력칸이_모두_들어_있다(self):
        expected = {
            "create-title",
            "create-housing-name",
            "create-area-sqm",
            "create-recruitment-count",
            "create-location",
            "create-deposit",
            "create-monthly-rent",
            "create-start-date",
            "create-end-date",
            "create-description",
            "create-image",
            "create-source-url",
        }
        self.assertEqual(set(CREATE_FORM_KEYS), expected)

    def test_이름이_겹치지_않는다(self):
        self.assertEqual(len(CREATE_FORM_KEYS), len(set(CREATE_FORM_KEYS)))

    def test_모두_create_로_시작한다(self):
        """다른 화면의 값과 헷갈리지 않도록 이름 앞을 맞춥니다."""
        self.assertTrue(all(key.startswith("create-") for key in CREATE_FORM_KEYS))


class ResetFormStateTest(unittest.TestCase):
    def test_입력값을_모두_지운다(self):
        state = filled_state()

        cleared = reset_form_state(state)

        self.assertEqual(state, {})
        self.assertEqual(set(cleared), set(CREATE_FORM_KEYS))

    def test_등록_폼과_상관없는_값은_지우지_않는다(self):
        """로그인 정보처럼 다른 값까지 지우면 화면이 로그아웃됩니다."""
        state = filled_state()
        state.update({"loginout": "login", "admin_username": "tester"})

        reset_form_state(state)

        self.assertEqual(state, {"loginout": "login", "admin_username": "tester"})

    def test_값이_없어도_오류가_나지_않는다(self):
        state = {}

        cleared = reset_form_state(state)

        self.assertEqual(cleared, [])
        self.assertEqual(state, {})

    def test_일부만_있어도_있는_것만_지운다(self):
        state = {"create-title": "제목", "loginout": "login"}

        cleared = reset_form_state(state)

        self.assertEqual(cleared, ["create-title"])
        self.assertEqual(state, {"loginout": "login"})

    def test_두_번_눌러도_안전하다(self):
        state = filled_state()

        reset_form_state(state)
        cleared_again = reset_form_state(state)

        self.assertEqual(cleared_again, [])
        self.assertEqual(state, {})

    def test_초기화하지_않으면_입력값이_남는다(self):
        """등록 뒤에도 값이 남아야 비슷한 공고를 이어서 넣을 수 있습니다."""
        state = filled_state()

        # 초기화를 부르지 않은 경우
        self.assertEqual(state["create-title"], "create-title 값")
        self.assertIn("create-image", state)


if __name__ == "__main__":
    unittest.main()
