# test_listing_extract.py
"""Gemini 추출 결과 확인 로직 테스트.

Gemini나 서버에 연결하지 않고, 모델이 돌려줄 법한 값만 흉내 내서 확인합니다.
실제 API 키는 쓰지 않습니다.
"""

import unittest

from core.constants import SEOUL_DISTRICTS
from core.listing_extract import summarize, validate_all, validate_extracted


def good_item(**overrides) -> dict:
    item = {
        "title": "2026년 도시형생활주택 잔여세대 입주자 모집공고",
        "housing_name": "방화동원룸(유니트로) 13㎡형",
        "area_sqm": 13.98,
        "recruitment_count": 14,
        "location": "강서구",
        "deposit": 10260000,
        "monthly_rent": 125500,
        "application_start_date": "2026-08-18",
        "application_end_date": "2026-08-20",
        "description": "신청자격 : 서울 거주 1인 무주택세대구성원",
        "source_url": "https://www.i-sh.co.kr/main/index.do",
    }
    item.update(overrides)
    return item


class ValidateExtractedTest(unittest.TestCase):
    def test_정상_값은_등록용_값으로_바뀐다(self):
        payload, problems = validate_extracted(good_item(), SEOUL_DISTRICTS)

        self.assertEqual(problems, [])
        self.assertEqual(payload["housing_name"], "방화동원룸(유니트로) 13㎡형")
        self.assertEqual(payload["area_sqm"], 13.98)
        self.assertEqual(payload["deposit"], 10260000)
        self.assertIsNone(payload["image_url"])

    def test_쉼표와_원_표기도_숫자로_읽는다(self):
        payload, problems = validate_extracted(
            good_item(deposit="10,260,000원", monthly_rent="125,500 원"), SEOUL_DISTRICTS
        )

        self.assertEqual(problems, [])
        self.assertEqual(payload["deposit"], 10260000)
        self.assertEqual(payload["monthly_rent"], 125500)

    def test_제곱미터_표기도_숫자로_읽는다(self):
        payload, _ = validate_extracted(good_item(area_sqm="13.98㎡"), SEOUL_DISTRICTS)
        self.assertEqual(payload["area_sqm"], 13.98)

    def test_점으로_구분한_날짜도_읽는다(self):
        payload, problems = validate_extracted(
            good_item(application_start_date="2026.08.18"), SEOUL_DISTRICTS
        )
        self.assertEqual(problems, [])
        self.assertEqual(payload["application_start_date"], "2026-08-18")

    def test_필수_값이_없으면_등록하지_않는다(self):
        payload, problems = validate_extracted(good_item(title=""), SEOUL_DISTRICTS)

        self.assertIsNone(payload)
        self.assertTrue(any("title" in p for p in problems))

    def test_서울_자치구가_아니면_막는다(self):
        payload, problems = validate_extracted(good_item(location="부산 해운대구"), SEOUL_DISTRICTS)

        self.assertIsNone(payload)
        self.assertTrue(any("자치구" in p for p in problems))

    def test_숫자가_아닌_금액은_막는다(self):
        payload, problems = validate_extracted(good_item(deposit="문의"), SEOUL_DISTRICTS)

        self.assertIsNone(payload)
        self.assertTrue(any("보증금" in p for p in problems))

    def test_면적이_0이면_막는다(self):
        payload, problems = validate_extracted(good_item(area_sqm=0), SEOUL_DISTRICTS)
        self.assertIsNone(payload)
        self.assertTrue(any("면적" in p for p in problems))

    def test_종료일이_시작일보다_빠르면_막는다(self):
        payload, problems = validate_extracted(
            good_item(application_end_date="2026-08-01"), SEOUL_DISTRICTS
        )

        self.assertIsNone(payload)
        self.assertTrue(any("빠릅니다" in p for p in problems))

    def test_날짜를_읽을_수_없으면_막는다(self):
        payload, problems = validate_extracted(
            good_item(application_end_date="미정"), SEOUL_DISTRICTS
        )
        self.assertIsNone(payload)
        self.assertTrue(any("종료일" in p for p in problems))

    def test_사전이_아니면_막는다(self):
        payload, problems = validate_extracted("이상한 값", SEOUL_DISTRICTS)
        self.assertIsNone(payload)
        self.assertEqual(len(problems), 1)

    def test_이미지는_자동으로_넣지_않는다(self):
        """PDF에서 뽑은 값으로 이미지를 지어내지 않습니다."""
        payload, _ = validate_extracted(good_item(image_url="https://지어낸주소"), SEOUL_DISTRICTS)
        self.assertIsNone(payload["image_url"])

    def test_등록_API가_받는_항목만_담는다(self):
        payload, _ = validate_extracted(good_item(사족="모델이 덧붙인 값"), SEOUL_DISTRICTS)
        self.assertEqual(
            set(payload),
            {
                "title", "housing_name", "area_sqm", "recruitment_count", "location",
                "deposit", "monthly_rent", "application_start_date",
                "application_end_date", "description", "image_url", "source_url",
            },
        )


class ValidateAllTest(unittest.TestCase):
    def test_여러_건을_한_번에_확인한다(self):
        results = validate_all([good_item(), good_item(title="")], SEOUL_DISTRICTS)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["problems"], [])
        self.assertTrue(results[1]["problems"])

    def test_목록이_아니면_빈_결과다(self):
        self.assertEqual(validate_all({"a": 1}, SEOUL_DISTRICTS), [])
        self.assertEqual(validate_all(None, SEOUL_DISTRICTS), [])

    def test_원본_값을_함께_돌려준다(self):
        results = validate_all([good_item()], SEOUL_DISTRICTS)
        self.assertEqual(results[0]["source"]["location"], "강서구")


class SummarizeTest(unittest.TestCase):
    def test_등록_가능_건수를_센다(self):
        results = validate_all([good_item(), good_item(), good_item(title="")], SEOUL_DISTRICTS)

        counts = summarize(results)

        self.assertEqual(counts, {"total": 3, "ready": 2, "blocked": 1})

    def test_빈_목록도_센다(self):
        self.assertEqual(summarize([]), {"total": 0, "ready": 0, "blocked": 0})


if __name__ == "__main__":
    unittest.main()
