# listing_service.py
from app.core.supabase_config import get_supabase
from app.schemas.listing_schema import ListingCreate, ListingPage, ListingPublic

# 목록을 페이지로 나눌 때 쓰는 값입니다.
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100


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


def listing_get_all() -> list[ListingPublic]:
    supabase = get_supabase()
    result = (
        supabase.table("listings")
        .select("*")
        .order("application_start_date", desc=True)
        .execute()
    )
    return [ListingPublic.model_validate(item) for item in result.data]


def listing_get_page(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> ListingPage:
    """등록이 최신인 순서로 한 페이지 분량만 가져옵니다.

    전체를 받아 와서 자르지 않고, Supabase에 정렬과 범위를 맡깁니다.
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
    result = (
        supabase.table("listings")
        .select("*")
        .order("created_at", desc=True)
        .order("id", desc=True)
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
) -> list[ListingPublic]:
    supabase = get_supabase()
    query = supabase.table("listings").select("*")

    if location:
        query = query.ilike("location", f"%{location}%")
    if max_deposit is not None:
        query = query.lte("deposit", max_deposit)
    if max_monthly_rent is not None:
        query = query.lte("monthly_rent", max_monthly_rent)

    result = query.order("application_start_date", desc=True).execute()
    return [ListingPublic.model_validate(item) for item in result.data]


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
