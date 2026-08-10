# listing_service.py
from datetime import date

from app.core.supabase_config import get_supabase
from app.schemas.listing_schema import ListingCreate, ListingPage, ListingPublic

# 목록을 페이지로 나눌 때 쓰는 값입니다.
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# 화면에서 고를 수 있는 정렬 기준입니다.
# 이름 -> (정렬에 쓸 컬럼, 내림차순 여부)
# 정렬을 화면에서 하지 않고 여기서 하는 이유가 있습니다.
# 관리자 목록은 한 번에 한 페이지(10건)만 받아 가는데,
# 받은 10건만 다시 늘어놓으면 전체 기준의 순서가 아니기 때문입니다.
SORT_COLUMNS = {
    "created_desc": ("created_at", True),
    "end_date_asc": ("application_end_date", False),
    "area_desc": ("area_sqm", True),
    "area_asc": ("area_sqm", False),
    "recruitment_desc": ("recruitment_count", True),
    "recruitment_asc": ("recruitment_count", False),
    "deposit_desc": ("deposit", True),
    "deposit_asc": ("deposit", False),
    "rent_desc": ("monthly_rent", True),
    "rent_asc": ("monthly_rent", False),
}


def apply_sort(query, sort: str | None):
    """고른 기준으로 정렬을 붙입니다.

    값이 비어 있는 공고는 어떤 기준이든 맨 뒤로 보냅니다(nullsfirst=False).
    같은 값끼리는 나중에 등록한 공고를 앞에 두어 순서가 흔들리지 않게 합니다.
    """

    column, desc = SORT_COLUMNS[sort]
    return query.order(column, desc=desc, nullsfirst=False).order("id", desc=True)


def is_known_sort(sort: str | None) -> bool:
    """화면이 보낸 정렬 기준을 아는지 확인합니다."""

    return sort in SORT_COLUMNS


def listing_create(listing: ListingCreate) -> ListingPublic | None:
    supabase = get_supabase()

    # mode="json"으로 바꾸면 date는 "2026-08-07", Decimal은 "39.72" 같은
    # 문자열이 되어 Supabase가 그대로 받을 수 있습니다.
    listing_data = listing.model_dump(mode="json")

    result = (
        supabase.table("listings")
        .insert(listing_data)
        .execute()
    )
    if not result.data:
        return None
    return ListingPublic.model_validate(result.data[0])


def listing_update(listing_id: int, listing: ListingCreate) -> ListingPublic | None:
    supabase = get_supabase()

    # 등록과 같은 방식으로 date와 Decimal을 Supabase가 받을 수 있는 값으로 바꿉니다.
    listing_data = listing.model_dump(mode="json")

    result = (
        supabase.table("listings")
        .update(listing_data)
        .eq("id", listing_id)
        .execute()
    )
    if not result.data:
        return None
    return ListingPublic.model_validate(result.data[0])


def listing_clear_image(listing_id: int) -> ListingPublic | None:
    """공고에서 이미지 참조만 지웁니다.

    image_url 한 칸만 건드립니다. 제목이나 금액 같은 다른 값은 보내지 않으므로,
    관리자가 화면에 입력만 해 두고 아직 저장하지 않은 값이 함께 저장될 일이 없습니다.

    Storage 파일 삭제는 여기서 하지 않습니다. DB가 먼저 바뀐 것을 확인한 뒤에
    호출한 쪽에서 image_service로 지웁니다.
    """

    supabase = get_supabase()
    result = (
        supabase.table("listings")
        .update({"image_url": None})
        .eq("id", listing_id)
        .execute()
    )
    if not result.data:
        return None
    return ListingPublic.model_validate(result.data[0])


def move_closed_to_end(
    listings: list[ListingPublic],
    today: date | None = None,
    recent_closed_first: bool = True,
) -> list[ListingPublic]:
    """신청이 끝난 공고를 목록 맨 뒤로 보냅니다.

    아직 신청할 수 있는 공고를 먼저 보여 주려는 것입니다.
    끝난 공고끼리의 순서는 무엇으로 정렬했는지에 따라 다릅니다.

    마감일 순으로 받았다면 뒤집어야 최근에 끝난 것부터가 됩니다.
    면적이나 보증금 순으로 받았다면 그 순서를 그대로 두어야 하므로,
    그때는 recent_closed_first를 False로 넘깁니다.
    """

    if today is None:
        today = date.today()

    still_open: list[ListingPublic] = []
    closed: list[ListingPublic] = []

    for listing in listings:
        end_date = listing.application_end_date
        if end_date is not None and end_date < today:
            closed.append(listing)
        else:
            still_open.append(listing)

    if recent_closed_first:
        # 들어온 순서가 마감일 오름차순이므로, 뒤집으면 최근에 끝난 것부터가 됩니다.
        closed.reverse()
    return still_open + closed


def listing_get_all(sort: str | None = None) -> list[ListingPublic]:
    """기본은 마감이 가까운 순으로 돌려줍니다.

    같은 날 마감이면 나중에 등록한 공고를 앞에 둡니다.
    이미 신청이 끝난 공고는 어떤 기준으로 정렬하든 맨 뒤로 보냅니다.
    """
    supabase = get_supabase()
    query = supabase.table("listings").select("*")

    # 마감일 순은 등록 시각까지 함께 보므로 따로 둡니다.
    if sort is None or sort == "end_date_asc":
        result = (
            query.order("application_end_date")
            .order("created_at", desc=True)
            .order("id", desc=True)
            .execute()
        )
        recent_closed_first = True
    else:
        result = apply_sort(query, sort).execute()
        # 고른 기준의 순서를 흐트러뜨리지 않도록 끝난 공고도 그대로 둡니다.
        recent_closed_first = False

    listings = [ListingPublic.model_validate(item) for item in result.data]
    return move_closed_to_end(listings, recent_closed_first=recent_closed_first)


def listing_get_page(
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort: str | None = None,
) -> ListingPage:
    """고른 기준으로 한 페이지 분량만 가져옵니다. 기본은 등록이 최신인 순서입니다.

    전체를 받아 와서 자르지 않고, Supabase에 정렬과 범위를 맡깁니다.
    정렬을 서버에 맡겨야 페이지를 넘겨도 전체 기준의 순서가 이어집니다.
    """

    supabase = get_supabase()

    # 값이 이상하게 들어와도 안전한 범위로 맞춥니다.
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    page = max(1, page)

    # 전체 개수를 먼저 셉니다.
    # 범위를 넘는 페이지를 요청하면 Supabase가 오류를 내기 때문에,
    # 개수를 알고 나서 안전한 페이지로 맞춘 뒤 목록을 가져옵니다.
    count_result = (
        supabase.table("listings")
        .select("id", count="exact")
        .limit(1)
        .execute()
    )
    total_count = count_result.count or 0
    total_pages = max(1, -(-total_count // page_size))  # 올림 나눗셈

    # 마지막 공고를 지운 뒤처럼 페이지가 범위를 넘으면 마지막 페이지를 보여줍니다.
    page = min(page, total_pages)

    if total_count == 0:
        return ListingPage(
            items=[],
            page=page,
            page_size=page_size,
            total_count=0,
            total_pages=total_pages,
        )

    # 등록 시각이 같은 공고가 있어도 순서가 흔들리지 않도록 id로 한 번 더 정렬합니다.
    start = (page - 1) * page_size
    query = supabase.table("listings").select("*")
    result = (
        apply_sort(query, sort or "created_desc")
        .range(start, start + page_size - 1)
        .execute()
    )

    return ListingPage(
        items=[ListingPublic.model_validate(item) for item in result.data],
        page=page,
        page_size=page_size,
        total_count=total_count,
        total_pages=total_pages,
    )


def listing_get(listing_id: int) -> ListingPublic | None:
    supabase = get_supabase()
    result = (
        supabase.table("listings")
        .select("*")
        .eq("id", listing_id)
        .execute()
    )
    if not result.data:
        return None
    return ListingPublic.model_validate(result.data[0])


def listing_search(
    location: str | None,
    max_deposit: int | None,
    max_monthly_rent: int | None,
    sort: str | None = None,
) -> list[ListingPublic]:
    supabase = get_supabase()
    query = supabase.table("listings").select("*")

    if location:
        query = query.ilike("location", f"%{location}%")
    if max_deposit is not None:
        query = query.lte("deposit", max_deposit)
    if max_monthly_rent is not None:
        query = query.lte("monthly_rent", max_monthly_rent)

    # 목록과 같은 기준입니다. 기본은 마감이 가까운 순, 같으면 등록이 최신인 순입니다.
    if sort is None or sort == "end_date_asc":
        result = (
            query.order("application_end_date")
            .order("created_at", desc=True)
            .order("id", desc=True)
            .execute()
        )
        recent_closed_first = True
    else:
        result = apply_sort(query, sort).execute()
        recent_closed_first = False

    listings = [ListingPublic.model_validate(item) for item in result.data]
    return move_closed_to_end(listings, recent_closed_first=recent_closed_first)


def listing_delete(listing_id: int) -> ListingPublic | None:
    supabase = get_supabase()
    result = (
        supabase.table("listings")
        .delete()
        .eq("id", listing_id)
        .execute()
    )
    if not result.data:
        return None
    return ListingPublic.model_validate(result.data[0])
