# listing_service.py
from app.core.supabase_config import get_supabase
from app.schemas.listing_schema import ListingCreate, ListingPublic


def listing_create(listing: ListingCreate) -> ListingPublic | None:
    supabase = get_supabase()

    result = (
        supabase.table("listings")
        .insert(
            {
                "title": listing.title,
                "type": listing.type,
                "location": listing.location,
                "price": listing.price,
                "eligibility": listing.eligibility,
                "image_url": listing.image_url,
                "source_url": listing.source_url,
                "announced_at": listing.announced_at.isoformat() if listing.announced_at else None,
                "deadline": listing.deadline.isoformat() if listing.deadline else None,
                "description": listing.description,
            }
        )
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
        .order("announced_at", desc=True)
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
    type: str | None,
    location: str | None,
    min_price: int | None,
    max_price: int | None,
    eligibility: str | None,
) -> list[ListingPublic]:
    supabase = get_supabase()
    query = supabase.table("listings").select("*")

    if type:
        query = query.eq("type", type)
    if location:
        query = query.ilike("location", f"%{location}%")
    if min_price is not None:
        query = query.gte("price", min_price)
    if max_price is not None:
        query = query.lte("price", max_price)
    if eligibility:
        query = query.ilike("eligibility", f"%{eligibility}%")

    result = query.order("announced_at", desc=True).execute()
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
