# gemini_client.py
"""Gemini에 공고 PDF를 보내 청약정보를 뽑아냅니다.

주의: 이 파일은 실제 Gemini API 키가 없어 아직 실행 검증을 하지 못했습니다.
키를 넣고 처음 쓸 때는 결과를 반드시 사람이 확인해 주세요.
호출부를 이 함수 하나로 모아 두었으므로, SDK 사용법이 다르면 여기만 고치면 됩니다.
"""

import json

from core.gemini_config import get_api_key, get_model_name


class GeminiError(RuntimeError):
    """Gemini 호출이 실패했을 때 화면에 보여 줄 오류입니다."""


# 모델에게 요구하는 출력 형태입니다. 등록 API가 받는 항목과 이름을 맞춥니다.
EXTRACT_PROMPT = """당신은 공공임대 청약 공고 PDF에서 등록용 정보를 뽑아내는 도구입니다.

아래 규칙을 지켜 JSON 배열만 출력하세요. 설명 문장은 쓰지 마세요.

- 배열의 각 원소는 '주택 1개 + 전용면적(주택형) 1개'입니다.
  같은 공고라도 주택이나 면적이 다르면 원소를 나눕니다.
- 각 원소는 다음 항목을 가집니다.
  title: 공고명
  housing_name: 주택명과 주택형 (예: "방화동원룸(유니트로) 13㎡형")
  area_sqm: 전용면적 숫자만 (예: 13.98)
  recruitment_count: 모집 호수 숫자만
  location: 서울 자치구 이름 (예: "강서구")
  detail_address: 그 주택의 도로명 주소 (예: "강서구 개화동로21길 49")
  deposit: 임대보증금 원 단위 숫자만
  monthly_rent: 월 임대료 원 단위 숫자만
  application_start_date: 신청 시작일 YYYY-MM-DD
  application_end_date: 신청 종료일 YYYY-MM-DD
  description: 신청자격, 소득기준, 자산기준, 공급 구성, 주의사항을 줄바꿈으로 나눈 항목형 설명
  source_url: 공고 원문 주소 (PDF에서 찾을 수 없으면 빈 문자열)
  page: 이 주택의 위치도(지도 그림)가 실린 쪽 번호. 없으면 null
- 값을 찾을 수 없으면 지어내지 말고 빈 문자열이나 null을 넣으세요.
- 금액에 쉼표나 '원'을 붙이지 마세요.
- 표에서 주택형 이름 칸이 비어 있어도 면적과 금액이 다르면 별개의 원소로 만드세요.
  칸이 병합되어 이름이 생략된 줄을 빠뜨리지 마세요.
"""

# 모델이 돌려줄 형태를 못 박아 둡니다.
# 형식을 지정하지 않으면 항목 이름이나 자료형이 조금씩 달라져
# 아래 확인 단계에서 걸리는 일이 생깁니다.
EXTRACT_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING"},
            "housing_name": {"type": "STRING"},
            "area_sqm": {"type": "NUMBER", "nullable": True},
            "recruitment_count": {"type": "INTEGER", "nullable": True},
            "location": {"type": "STRING"},
            "detail_address": {"type": "STRING", "nullable": True},
            "deposit": {"type": "INTEGER", "nullable": True},
            "monthly_rent": {"type": "INTEGER", "nullable": True},
            "application_start_date": {"type": "STRING", "nullable": True},
            "application_end_date": {"type": "STRING", "nullable": True},
            "description": {"type": "STRING"},
            "source_url": {"type": "STRING", "nullable": True},
            "page": {"type": "INTEGER", "nullable": True},
        },
        "required": ["title", "housing_name", "location", "description"],
    },
}


def extract_listings_from_pdf(pdf_bytes: bytes, filename: str = "notice.pdf") -> list:
    """공고 PDF에서 청약정보 목록을 뽑아냅니다.

    돌려주는 값은 사전들의 목록입니다. 확인은 core.listing_extract가 맡습니다.
    """

    api_key = get_api_key()
    if not api_key:
        raise GeminiError(
            "Gemini API 키가 없습니다. FE_Admin/.env에 GEMINI_API_KEY를 넣어 주세요."
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError as error:
        raise GeminiError(
            "google-genai 패키지가 설치되어 있지 않습니다. "
            "FE_Admin/requirements.txt를 설치해 주세요."
        ) from error

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=get_model_name(),
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                EXTRACT_PROMPT,
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": EXTRACT_SCHEMA,
            },
        )
        text = (response.text or "").strip()
    except Exception as error:
        # 키 값이 섞여 나오지 않도록 오류 종류만 알려 줍니다.
        raise GeminiError(f"Gemini 호출에 실패했습니다. ({type(error).__name__})") from error

    return parse_extract_response(text)


def parse_extract_response(text: str) -> list:
    """모델이 돌려준 문자열에서 JSON 배열을 꺼냅니다.

    앞뒤에 코드 블록 표시가 붙어 오는 경우가 있어 걷어냅니다.
    """

    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[: -3]
        cleaned = cleaned.strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

    if not cleaned:
        raise GeminiError("Gemini가 빈 응답을 돌려주었습니다.")

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as error:
        raise GeminiError("Gemini 응답을 JSON으로 읽을 수 없습니다.") from error

    if isinstance(parsed, dict):
        # {"listings": [...]} 형태로 올 수도 있어 배열을 찾아 씁니다.
        for value in parsed.values():
            if isinstance(value, list):
                return value
        return [parsed]

    if not isinstance(parsed, list):
        raise GeminiError("Gemini 응답이 목록 형태가 아닙니다.")

    return parsed
