# test_page_params.py
"""URL query parameter 변환 함수 테스트.

Streamlit이나 서버에 연결하지 않는 순수 함수만 확인합니다.
FE_Admin 폴더에서 아래 명령으로 실행합니다.

    python -m unittest discover -s tests
"""

import unittest

from core.page_params import build_params, parse_edit_id, parse_page, parse_search


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


class ParseSearchTest(unittest.TestCase):
    def test_검색_조건이_없으면_빈_사전이다(self):
        self.assertEqual(parse_search({}), {})

    def test_자치구를_읽는다(self):
        self.assertEqual(parse_search({"location": ["강남구"]}), {"location": "강남구"})

    def test_금액을_읽는다(self):
        parsed = parse_search({"max_deposit": ["20000000"], "max_monthly_rent": ["300000"]})
        self.assertEqual(parsed, {"max_deposit": "20000000", "max_monthly_rent": "300000"})

    def test_0이나_음수_금액은_조건이_아니다(self):
        self.assertEqual(parse_search({"max_deposit": ["0"], "max_monthly_rent": ["-1"]}), {})

    def test_숫자가_아닌_금액은_무시한다(self):
        self.assertEqual(parse_search({"max_deposit": ["abc"]}), {})

    def test_빈_자치구는_조건이_아니다(self):
        self.assertEqual(parse_search({"location": ["  "]}), {})

    def test_같은_이름이_여러_번_오면_첫_값을_쓴다(self):
        self.assertEqual(parse_search({"location": ["강남구", "중구"]}), {"location": "강남구"})

    def test_검색_조건_외의_값은_읽지_않는다(self):
        parsed = parse_search({"location": ["강남구"], "edit_id": ["13"], "page": ["5"]})
        self.assertEqual(parsed, {"location": "강남구"})


class BuildParamsWithSearchTest(unittest.TestCase):
    """수정 화면을 오갈 때 검색 조건이 주소에 남아야 뒤로가기로 돌아와도 유지됩니다."""

    def test_검색_조건을_함께_담는다(self):
        params = build_params(1, None, {"location": "강남구", "max_deposit": "20000000"})
        self.assertEqual(
            params, {"page": "1", "location": "강남구", "max_deposit": "20000000"}
        )

    def test_수정_중에도_검색_조건이_남는다(self):
        params = build_params(1, 136, {"max_deposit": "20000000"})
        self.assertEqual(
            params, {"page": "1", "edit_id": "136", "max_deposit": "20000000"}
        )

    def test_수정_화면을_닫아도_검색_조건은_남는다(self):
        search = {"location": "강남구"}
        opened = build_params(3, 136, search)
        closed = build_params(3, None, search)
        self.assertEqual(closed, {"page": "3", "location": "강남구"})
        self.assertNotIn("edit_id", closed)
        self.assertEqual(opened["location"], closed["location"])

    def test_검색_조건이_없으면_기존과_같다(self):
        self.assertEqual(build_params(5, 123, None), build_params(5, 123))
        self.assertEqual(build_params(5, 123, {}), build_params(5, 123))

    def test_빈_값은_담지_않는다(self):
        self.assertEqual(build_params(1, None, {"location": "  "}), {"page": "1"})

    def test_검색_조건_외의_값은_담지_않는다(self):
        params = build_params(1, None, {"location": "강남구", "password": "비밀"})
        self.assertEqual(set(params), {"page", "location"})

    def test_주소에_다시_읽어도_같은_조건이_나온다(self):
        search = {"location": "강남구", "max_deposit": "20000000"}
        params = build_params(2, 136, search)
        restored = parse_search({k: [v] for k, v in params.items()})
        self.assertEqual(restored, search)


if __name__ == "__main__":
    unittest.main()
