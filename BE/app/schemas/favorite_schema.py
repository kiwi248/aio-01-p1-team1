# favorite_schema.py
from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.listing_schema import ListingPublic


class FavoriteCreate(BaseModel):
    user_id: str
    listing_id: int


class FavoritePublic(BaseModel):
    id: int
    user_id: str
    listing_id: int
    created_at: datetime


class FavoriteWithListing(BaseModel):
    id: int
    user_id: str
    listing_id: int
    created_at: datetime
    listing: ListingPublic


class FavoriteRanking(BaseModel):
    listing_id: int
    title: str
    deadline: date | None = None
    is_expired: bool
    favorite_count: int


class FavoriteDetail(BaseModel):
    favorite_id: int
    user_id: str
    nickname: str | None = None
    listing_id: int
    title: str
    created_at: datetime
