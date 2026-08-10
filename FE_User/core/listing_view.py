# listing_view.py
"""청약정보를 화면에 보여줄 때 쓰는 문구를 만듭니다.

같은 공고 안에 주택형이 여러 개라 공고명이 전부 같습니다.
그래서 목록에서는 주택명을 앞세우고, 나머지 정보는 짧게 끊어 보여 줍니다.

Streamlit에 기대지 않는 순수 함수라 테스트하기 쉽습니다.
"""

from core.area_format import format_area


def card_title(listing: dict) -> str:
    """카드 제목입니다. 주택명이 없으면 공고명을 대신 씁니다."""

    housing_name = (listing.get("housing_name") or "").strip()
    if housing_name:
        return housing_name

    title = (listing.get("title") or "").strip()
    return title or "제목 없음"


def format_won(value: object) -> str:
    """금액에 세 자리마다 쉼표를 넣습니다."""

    try:
        return f"{int(value):,}원"
    except (TypeError, ValueError):
        return "-"


def summary_line(listing: dict) -> str:
    """자치구·전용면적·모집 인원을 한 줄로 묶습니다.

    값이 없는 항목은 빼서 "-  ·  -" 같은 문구가 나오지 않게 합니다.
    """

    parts = []

    location = (listing.get("location") or "").strip()
    if location:
        parts.append(location)

    area = listing.get("area_sqm")
    if area not in (None, ""):
        parts.append(f"전용 {format_area(area)}")

    count = listing.get("recruitment_count")
    if count not in (None, ""):
        parts.append(f"{count}호 모집")

    return "  ·  ".join(parts)


def address_line(listing: dict) -> str:
    """상세주소 줄입니다. 주소가 없으면 빈 문구입니다."""

    address = (listing.get("detail_address") or "").strip()
    return f"📍 {address}" if address else ""


def period_line(listing: dict) -> str:
    """신청 기간을 한 줄로 만듭니다."""

    start = listing.get("application_start_date") or "-"
    end = listing.get("application_end_date") or "-"
    return f"신청 {start} ~ {end}"


def dday_badge(remaining: object, closed: bool, urgent_days: int = 3) -> str:
    """남은 날수를 눈에 띄는 표시로 바꿉니다.

    마감이 코앞이면 붉게, 여유가 있으면 푸르게, 끝났으면 흐리게 보여 줍니다.
    남은 날수를 모르면 빈 문구입니다.
    """

    label = "" if remaining is None else str(remaining).strip()
    if not label:
        return ""

    if closed:
        return f":gray[{label}]"

    if label == "D-DAY":
        return f":red[**{label}**]"

    if label.startswith("D-"):
        try:
            days = int(label[2:])
        except ValueError:
            return f":blue[**{label}**]"
        if days <= urgent_days:
            return f":red[**{label}**]"

    return f":blue[**{label}**]"


def description_preview(listing: dict, limit: int = 60) -> str:
    """상세 설명의 첫 줄만 짧게 보여 줍니다.

    설명이 길어 목록이 늘어지므로, 자세한 내용은 펼쳐 보게 합니다.
    """

    description = (listing.get("description") or "").strip()
    if not description:
        return ""

    first_line = description.splitlines()[0].strip()
    if len(first_line) <= limit:
        return first_line

    return first_line[:limit].rstrip() + "…"
