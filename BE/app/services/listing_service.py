# listing_service.py
from app.core.supabase_config import get_supabase
from app.schemas.listing_schema import ListingCreate, ListingPublic


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
