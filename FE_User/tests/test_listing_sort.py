# test_listing_sort.py
"""청약정보 목록 정렬 테스트."""

import unittest

from core.listing_sort import (
    DEFAULT_SORT,
    SORT_OPTIONS,
    sort_key_of,
    sort_listings,
)


def sample_listings() -> list:
    return [
        {
            "id": 1,
            "housing_name": "가",
            "area_sqm": "13.98",
            "recruitment_count": 14,
            "deposit": 10260000,
            "monthly_rent": 125500,
            "application_end_date": "2026-08-20",
        },
        {
            "id": 2,
            "housing_name": "나",
            "area_sqm": "33.83",
            "recruitment_count": 1,
            "deposit": 50000000,
            "monthly_rent": 90000,
            "application_end_date": "2026-08-15",
        },
        {
            "id": 3,
            "housing_name": "다",
            "area_sqm": "19.08",
            "recruitment_count": 4,
            "deposit": 20000000,
            "monthly_rent": 300000,
            "application_end_date": "2026-09-01",
        },
    ]


def names(listings) -> list:
    return [x["housing_name"] for x in listings]


class SortOptionsTest(unittest.TestCase):
    def test_요청한_정렬_기준이_모두_있다(self):
        for option in (
            "면적 넓은 순",
            "면적 좁은 순",
            "모집인원 많은 순",
            "모집인원 적은 순",
            "보증금 높은 순",
            "보증금 낮은 순",
            "월세 높은순",
            "월세 낮은순",
            "신청 종료일 빠른순",
        ):
            self.assertIn(option, SORT_OPTIONS)

    def test_기본값은_최신_등록순이다(self):
        self.assertEqual(DEFAULT_SORT, "최신 등록순")
        self.assertEqual(SORT_OPTIONS[0], DEFAULT_SORT)

    def test_선택지_이름이_겹치지_않는다(self):
        self.assertEqual(len(SORT_OPTIONS), len(set(SORT_OPTIONS)))


class SortListingsTest(unittest.TestCase):
    def test_면적_넓은_순(self):
        self.assertEqual(names(sort_listings(sample_listings(), "면적 넓은 순")), ["나", "다", "가"])

    def test_면적_좁은_순(self):
        self.assertEqual(names(sort_listings(sample_listings(), "면적 좁은 순")), ["가", "다", "나"])

    def test_모집인원_많은_순(self):
        self.assertEqual(
            names(sort_listings(sample_listings(), "모집인원 많은 순")), ["가", "다", "나"]
        )

    def test_모집인원_적은_순(self):
        self.assertEqual(
            names(sort_listings(sample_listings(), "모집인원 적은 순")), ["나", "다", "가"]
        )

    def test_보증금_높은_순(self):
        self.assertEqual(names(sort_listings(sample_listings(), "보증금 높은 순")), ["나", "다", "가"])

    def test_보증금_낮은_순(self):
        self.assertEqual(names(sort_listings(sample_listings(), "보증금 낮은 순")), ["가", "다", "나"])

    def test_월세_높은순(self):
        self.assertEqual(names(sort_listings(sample_listings(), "월세 높은순")), ["다", "가", "나"])

    def test_월세_낮은순(self):
        self.assertEqual(names(sort_listings(sample_listings(), "월세 낮은순")), ["나", "가", "다"])

    def test_신청_종료일_빠른순(self):
        self.assertEqual(
            names(sort_listings(sample_listings(), "신청 종료일 빠른순")), ["나", "가", "다"]
        )

    def test_최신_등록순은_id가_큰_순이다(self):
        self.assertEqual(names(sort_listings(sample_listings(), "최신 등록순")), ["다", "나", "가"])


class MissingValueTest(unittest.TestCase):
    def test_값이_없는_공고는_항상_뒤로_간다(self):
        listings = sample_listings() + [{"id": 9, "housing_name": "빈값"}]

        for option in SORT_OPTIONS:
            if option == DEFAULT_SORT:
                continue
            self.assertEqual(
                names(sort_listings(listings, option))[-1], "빈값", f"기준 {option}"
            )

    def test_숫자가_아닌_값도_뒤로_간다(self):
        listings = sample_listings() + [{"id": 9, "housing_name": "이상", "area_sqm": "미정"}]

        self.assertEqual(names(sort_listings(listings, "면적 넓은 순"))[-1], "이상")

    def test_날짜가_아닌_값도_뒤로_간다(self):
        listings = sample_listings() + [
            {"id": 9, "housing_name": "이상", "application_end_date": "미정"}
        ]

        self.assertEqual(names(sort_listings(listings, "신청 종료일 빠른순"))[-1], "이상")


class TieBreakTest(unittest.TestCase):
    def test_값이_같으면_등록이_최신인_공고가_앞이다(self):
        listings = [
            {"id": 1, "housing_name": "먼저", "deposit": 1000},
            {"id": 2, "housing_name": "나중", "deposit": 1000},
        ]

        self.assertEqual(names(sort_listings(listings, "보증금 높은 순")), ["나중", "먼저"])
        self.assertEqual(names(sort_listings(listings, "보증금 낮은 순")), ["나중", "먼저"])


class SafetyTest(unittest.TestCase):
    def test_원래_목록을_바꾸지_않는다(self):
        listings = sample_listings()
        before = names(listings)

        sort_listings(listings, "면적 넓은 순")

        self.assertEqual(names(listings), before)

    def test_건수가_줄지_않는다(self):
        listings = sample_listings()
        self.assertEqual(len(sort_listings(listings, "월세 높은순")), len(listings))

    def test_모르는_기준이면_기본값으로_정렬한다(self):
        self.assertEqual(
            names(sort_listings(sample_listings(), "없는 기준")),
            names(sort_listings(sample_listings(), DEFAULT_SORT)),
        )

    def test_목록이_아니면_빈_결과다(self):
        self.assertEqual(sort_listings(None), [])
        self.assertEqual(sort_listings({"a": 1}), [])

    def test_사전이_아닌_항목은_걸러진다(self):
        self.assertEqual(len(sort_listings([{"id": 1}, "이상한 값", None])), 1)


class SortKeyTest(unittest.TestCase):
    def test_문자열_숫자도_읽는다(self):
        self.assertEqual(sort_key_of({"area_sqm": "13.98"}, "area_sqm"), 13.98)

    def test_읽을_수_없으면_None이다(self):
        self.assertIsNone(sort_key_of({"area_sqm": "미정"}, "area_sqm"))
        self.assertIsNone(sort_key_of({}, "deposit"))

    def test_날짜를_숫자로_바꾼다(self):
        earlier = sort_key_of({"application_end_date": "2026-08-15"}, "application_end_date")
        later = sort_key_of({"application_end_date": "2026-09-01"}, "application_end_date")
        self.assertLess(earlier, later)


if __name__ == "__main__":
    unittest.main()
