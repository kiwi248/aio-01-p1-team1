# test_image_action.py
"""공고 수정 시 이미지 동작 결정 로직 테스트.

Streamlit이나 서버에 연결하지 않는 순수 함수만 확인합니다.
FE_Admin 폴더에서 아래 명령으로 실행합니다.

    python -m unittest discover -s tests
"""

import unittest

from core.image_action import (
    CONFLICT,
    KEEP,
    REMOVE,
    REPLACE,
    build_image_fields,
    decide_image_action,
)


class DecideImageActionTest(unittest.TestCase):
    def test_새_이미지도_삭제도_없으면_기존_이미지를_유지한다(self):
        self.assertEqual(
            decide_image_action(has_new_image=False, remove_selected=False), KEEP
        )

    def test_새_이미지를_올리면_교체한다(self):
        self.assertEqual(
            decide_image_action(has_new_image=True, remove_selected=False), REPLACE
        )

    def test_삭제를_고르고_새_이미지가_없으면_삭제한다(self):
        self.assertEqual(
            decide_image_action(has_new_image=False, remove_selected=True), REMOVE
        )

    def test_새_이미지와_삭제를_함께_고르면_충돌이다(self):
        """한쪽을 조용히 무시하면 관리자가 결과를 예측할 수 없습니다."""
        self.assertEqual(
            decide_image_action(has_new_image=True, remove_selected=True), CONFLICT
        )

    def test_충돌은_교체나_삭제로_처리되지_않는다(self):
        action = decide_image_action(has_new_image=True, remove_selected=True)
        self.assertNotIn(action, (REPLACE, REMOVE, KEEP))


class BuildImageFieldsTest(unittest.TestCase):
    def test_삭제일_때만_remove_image가_참이다(self):
        self.assertEqual(build_image_fields(REMOVE), {"remove_image": "true"})

    def test_유지면_remove_image가_거짓이다(self):
        self.assertEqual(build_image_fields(KEEP), {"remove_image": "false"})

    def test_교체면_remove_image가_거짓이다(self):
        """교체는 새 파일로 덮어쓰므로 삭제 요청을 함께 보내지 않습니다."""
        self.assertEqual(build_image_fields(REPLACE), {"remove_image": "false"})

    def test_값은_폼으로_보낼_수_있는_문자열이다(self):
        for action in (KEEP, REPLACE, REMOVE):
            fields = build_image_fields(action)
            self.assertTrue(all(isinstance(v, str) for v in fields.values()))

    def test_이미지_관련_값만_담는다(self):
        self.assertEqual(set(build_image_fields(REMOVE)), {"remove_image"})


class SaveFlowTest(unittest.TestCase):
    """저장 요청에 실제로 실려 가는 값을 확인합니다."""

    def _payload(self, has_new_image: bool, remove_selected: bool) -> dict:
        action = decide_image_action(
            has_new_image=has_new_image, remove_selected=remove_selected
        )
        if action == CONFLICT:
            return {}
        return {"title": "공고", **build_image_fields(action)}

    def test_유지_저장_요청(self):
        self.assertEqual(
            self._payload(False, False)["remove_image"], "false"
        )

    def test_삭제_저장_요청(self):
        self.assertEqual(self._payload(False, True)["remove_image"], "true")

    def test_교체_저장_요청(self):
        self.assertEqual(self._payload(True, False)["remove_image"], "false")

    def test_충돌이면_요청을_만들지_않는다(self):
        self.assertEqual(self._payload(True, True), {})

    def test_취소하면_어떤_이미지_요청도_만들지_않는다(self):
        """취소는 저장 흐름 자체를 타지 않으므로 요청이 생기지 않습니다."""
        canceled = True
        payload = None if canceled else self._payload(False, True)
        self.assertIsNone(payload)


if __name__ == "__main__":
    unittest.main()
