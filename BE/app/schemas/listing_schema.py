# listing_schema.py
from datetime import date, datetime

from pydantic import BaseModel, Field


class ListingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255, examples=["행복주택 입주자 모집공고"])
    type: str | None = Field(default=None, max_length=50, examples=["공공임대"])
    location: str | None = Field(default=None, max_length=255, examples=["서울시 강남구"])
    price: int | None = Field(default=None, ge=0, examples=[50000000])
    eligibility: str | None = Field(default=None, examples=["무주택 세대주"])
    image_url: str | None = None
    source_url: str | None = None
    announced_at: date | None = None
    deadline: date | None = None
    description: str | None = None


class ListingPublic(BaseModel):
    id: int
    title: str
    type: str | None = None
    location: str | None = None
    price: int | None = None
    eligibility: str | None = None
    image_url: str | None = None
    source_url: str | None = None
    announced_at: date | None = None
    deadline: date | None = None
    description: str | None = None
    created_at: datetime
