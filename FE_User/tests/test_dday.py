# test_dday.py
"""신청 종료일 디데이 표시 테스트.

오늘 날짜를 직접 넘겨 확인하므로 실행하는 날과 상관없이 결과가 같습니다.
"""

import unittest
from datetime import date

from core.dday import days_left, dday_label, is_closed


TODAY = date(2026, 8, 10)


class DaysLeftTest(unittest.TestCase):
    def test_남은_날수를_센다(self):
        self.assertEqual(days_left("2026-08-20", TODAY), 10)
        self.assertEqual(days_left("2026-08-11", TODAY), 1)

    def test_오늘_마감이면_0이다(self):
        self.assertEqual(days_left("2026-08-10", TODAY), 0)

    def test_이미_지났으면_음수다(self):
        self.assertEqual(days_left("2026-08-05", TODAY), -5)

    def test_date_객체도_받는다(self):
        self.assertEqual(days_left(date(2026, 8, 20), TODAY), 10)

    def test_날짜로_읽을_수_없으면_None이다(self):
        for bad in (None, "", "abc", "2026-13-99", 123):
            self.assertIsNone(days_left(bad, TODAY), f"입력값 {bad!r}")


class DdayLabelTest(unittest.TestCase):
    def test_남았으면_D_빼기로_보여_준다(self):
        self.assertEqual(dday_label("2026-08-20", TODAY), "D-10")
        self.assertEqual(dday_label("2026-08-11", TODAY), "D-1")

    def test_오늘_마감이면_D_DAY다(self):
        self.assertEqual(dday_label("2026-08-10", TODAY), "D-DAY")

    def test_지났으면_마감이다(self):
        self.assertEqual(dday_label("2026-08-09", TODAY), "마감")

    def test_날짜를_모르면_아무것도_보여_주지_않는다(self):
        self.assertIsNone(dday_label(None, TODAY))
        self.assertIsNone(dday_label("abc", TODAY))


class IsClosedTest(unittest.TestCase):
    def test_지났으면_마감이다(self):
        self.assertTrue(is_closed("2026-08-09", TODAY))

    def test_오늘이나_이후면_마감이_아니다(self):
        self.assertFalse(is_closed("2026-08-10", TODAY))
        self.assertFalse(is_closed("2026-08-20", TODAY))

    def test_날짜를_모르면_마감으로_보지_않는다(self):
        """잘못된 값 때문에 신청할 수 있는 공고가 마감으로 보이면 안 됩니다."""
        self.assertFalse(is_closed(None, TODAY))
        self.assertFalse(is_closed("abc", TODAY))


class SortOrderTest(unittest.TestCase):
    """백엔드가 돌려주는 순서를 화면이 그대로 쓰는지 확인합니다."""

    def test_마감이_가까운_순서를_그대로_보여_준다(self):
        listings = [
            {"id": 1, "application_end_date": "2026-08-12"},
            {"id": 2, "application_end_date": "2026-08-10"},
            {"id": 3, "application_end_date": "2026-08-20"},
        ]
        labels = [dday_label(x["application_end_date"], TODAY) for x in listings]
        self.assertEqual(labels, ["D-2", "D-DAY", "D-10"])


if __name__ == "__main__":
    unittest.main()
