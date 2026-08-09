# listing_sort.py
"""청약정보 목록을 원하는 기준으로 다시 늘어놓습니다.

서버가 돌려준 목록을 화면에서 정렬합니다. 값이 비어 있는 공고는
어떤 기준으로 정렬하든 항상 뒤로 보내, 빈 값이 맨 위에 오지 않게 합니다.

Streamlit에 기대지 않는 순수 함수라 테스트하기 쉽습니다.
"""

from datetime import date

# 화면 선택지에 보여 줄 이름과 실제 기준입니다. 순서가 곧 화면 순서입니다.
SORT_OPTIONS = (
    "최신 등록순",
    "신청 종료일 빠른순",
    "면적 넓은 순",
    "면적 좁은 순",
    "모집인원 많은 순",
    "모집인원 적은 순",
    "보증금 높은 순",
    "보증금 낮은 순",
    "월세 높은순",
    "월세 낮은순",
)

DEFAULT_SORT = SORT_OPTIONS[0]

# 선택지 이름 -> (기준 항목, 내림차순 여부)
_RULES = {
    "최신 등록순": (None, True),
    "신청 종료일 빠른순": ("application_end_date", False),
    "면적 넓은 순": ("area_sqm", True),
    "면적 좁은 순": ("area_sqm", False),
    "모집인원 많은 순": ("recruitment_count", True),
    "모집인원 적은 순": ("recruitment_count", False),
    "보증금 높은 순": ("deposit", True),
    "보증금 낮은 순": ("deposit", False),
    "월세 높은순": ("monthly_rent", True),
    "월세 낮은순": ("monthly_rent", False),
}


def _to_number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_days(value: object) -> int | None:
    """날짜를 숫자로 바꿔 다른 기준과 같은 방식으로 비교합니다."""
    if isinstance(value, date):
        return value.toordinal()
    try:
        return date.fromisoformat(str(value)).toordinal()
    except (TypeError, ValueError):
        return None


def _listing_id(listing: dict) -> int:
    value = _to_number(listing.get("id"))
    return int(value) if value is not None else 0


def sort_key_of(listing: dict, field: str) -> float | None:
    """정렬에 쓸 값을 꺼냅니다. 읽을 수 없으면 None입니다."""

    if field == "application_end_date":
        days = _to_days(listing.get(field))
        return float(days) if days is not None else None

    return _to_number(listing.get(field))


def sort_listings(listings: object, option: str = DEFAULT_SORT) -> list:
    """고른 기준으로 목록을 다시 늘어놓습니다.

    같은 값이면 나중에 등록한 공고를 앞에 둡니다.
    값이 없는 공고는 기준과 상관없이 항상 뒤로 갑니다.
    """

    if not isinstance(listings, list):
        return []

    items = [x for x in listings if isinstance(x, dict)]
    field, desc = _RULES.get(option, _RULES[DEFAULT_SORT])

    if field is None:
        # 등록 최신순입니다. 서버가 준 순서를 믿지 않고 id로 다시 맞춥니다.
        return sorted(items, key=_listing_id, reverse=True)

    def ordering(listing: dict):
        value = sort_key_of(listing, field)
        missing = value is None
        # 값이 없으면 항상 뒤로 보냅니다.
        # 내림차순일 때는 부호를 뒤집어 한 번의 정렬로 처리합니다.
        ranked = 0.0 if missing else (-value if desc else value)
        return (missing, ranked, -_listing_id(listing))

    return sorted(items, key=ordering)
