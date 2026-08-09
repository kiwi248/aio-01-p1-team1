# test_listing_order.py
"""청약정보 조회 정렬 기준 테스트.

실제 Supabase에는 연결하지 않고, 어떤 정렬을 요청했는지만 확인합니다.
"""

import unittest
from unittest.mock import patch


class FakeQuery:
    """supabase 쿼리 빌더를 흉내 내며 order 호출을 기록합니다."""

    def __init__(self, log):
        self.log = log

    def select(self, *args, **kwargs):
        return self

    def ilike(self, *args, **kwargs):
        return self

    def lte(self, *args, **kwargs):
        return self

    def order(self, column, desc=False, **kwargs):
        self.log.append((column, desc))
        return self

    def execute(self):
        class Result:
            data = []

        return Result()


class FakeSupabase:
    def __init__(self, log):
        self.log = log

    def table(self, name):
        return FakeQuery(self.log)


class ListingOrderTest(unittest.TestCase):
    def _orders_for(self, call):
        from app.services import listing_service

        log = []
        with patch.object(listing_service, "get_supabase", return_value=FakeSupabase(log)):
            call(listing_service)
        return log

    def test_전체_조회는_마감이_가까운_순이다(self):
        orders = self._orders_for(lambda svc: svc.listing_get_all())

        self.assertEqual(orders[0], ("application_end_date", False))

    def test_전체_조회는_동률이면_등록_최신순이다(self):
        orders = self._orders_for(lambda svc: svc.listing_get_all())

        self.assertEqual(orders[1], ("created_at", True))
        self.assertEqual(orders[2], ("id", True))

    def test_검색도_같은_기준을_쓴다(self):
        orders = self._orders_for(
            lambda svc: svc.listing_search(
                location="강남구", max_deposit=None, max_monthly_rent=None
            )
        )

        self.assertEqual(
            orders, [("application_end_date", False), ("created_at", True), ("id", True)]
        )

    def test_시작일_기준_정렬은_더_이상_쓰지_않는다(self):
        orders = self._orders_for(lambda svc: svc.listing_get_all())

        self.assertNotIn("application_start_date", [column for column, _ in orders])

    def test_마감일은_오름차순이다(self):
        """가장 임박한 공고가 앞에 와야 하므로 내림차순이면 안 됩니다."""
        orders = self._orders_for(lambda svc: svc.listing_get_all())

        column, desc = orders[0]
        self.assertEqual(column, "application_end_date")
        self.assertFalse(desc)


if __name__ == "__main__":
    unittest.main()
