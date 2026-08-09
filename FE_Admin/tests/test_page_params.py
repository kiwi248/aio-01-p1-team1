# test_page_params.py
"""URL query parameter 변환 함수 테스트.

Streamlit이나 서버에 연결하지 않는 순수 함수만 확인합니다.
FE_Admin 폴더에서 아래 명령으로 실행합니다.

    python -m unittest discover -s tests
"""

import unittest

from core.page_params import build_params, parse_edit_id, parse_page


class ParsePageTest(unittest.TestCase):
    def test_정상적인_숫자는_그대로_쓴다(self):
        self.assertEqual(parse_page("5"), 5)
        self.assertEqual(parse_page("11"), 11)

    def test_값이_없으면_1페이지다(self):
        self.assertEqual(parse_page(None), 1)

    def test_숫자가_아니면_1페이지다(self):
        for bad in ("abc", "", "  ", "5.5", "1e3"):
            self.assertEqual(parse_page(bad), 1, f"입력값 {bad!r}")

    def test_0이나_음수는_1페이지다(self):
        self.assertEqual(parse_page("0"), 1)
        self.assertEqual(parse_page("-1"), 1)
        self.assertEqual(parse_page("-999"), 1)

    def test_앞뒤_공백은_무시한다(self):
        self.assertEqual(parse_page(" 7 "), 7)

    def test_같은_이름이_여러_번_오면_첫_값을_쓴다(self):
        self.assertEqual(parse_page(["3", "9"]), 3)

    def test_빈_목록은_1페이지다(self):
        self.assertEqual(parse_page([]), 1)

    def test_상한은_두지_않는다(self):
        """마지막 페이지를 넘는 값은 서버가 실제 개수를 보고 보정합니다."""
        self.assertEqual(parse_page("99999"), 99999)


class ParseEditIdTest(unittest.TestCase):
    def test_정상적인_ID는_그대로_쓴다(self):
        self.assertEqual(parse_edit_id("123"), 123)

    def test_값이_없으면_수정_모드가_아니다(self):
        self.assertIsNone(parse_edit_id(None))

    def test_숫자가_아니면_수정_모드가_아니다(self):
        for bad in ("abc", "", "  ", "12a", "1.5"):
            self.assertIsNone(parse_edit_id(bad), f"입력값 {bad!r}")

    def test_0이나_음수는_수정_모드가_아니다(self):
        self.assertIsNone(parse_edit_id("0"))
        self.assertIsNone(parse_edit_id("-5"))

    def test_같은_이름이_여러_번_오면_첫_값을_쓴다(self):
        self.assertEqual(parse_edit_id(["42", "77"]), 42)


class BuildParamsTest(unittest.TestCase):
    def test_수정_중이_아니면_page만_담는다(self):
        self.assertEqual(build_params(5), {"page": "5"})

    def test_수정_중이면_edit_id도_담는다(self):
        self.assertEqual(build_params(5, 123), {"page": "5", "edit_id": "123"})

    def test_페이지가_0이하여도_1로_맞춘다(self):
        self.assertEqual(build_params(0), {"page": "1"})
        self.assertEqual(build_params(-3), {"page": "1"})

    def test_값은_모두_문자열이다(self):
        params = build_params(2, 7)
        self.assertTrue(all(isinstance(v, str) for v in params.values()))

    def test_로그인_정보는_담기지_않는다(self):
        params = build_params(5, 123)
        self.assertEqual(set(params), {"page", "edit_id"})


if __name__ == "__main__":
    unittest.main()
