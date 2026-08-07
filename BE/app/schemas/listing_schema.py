# listing_schema.py
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ListingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255, examples=["행복주택 입주자 모집공고"])
    housing_name: str = Field(min_length=1, max_length=255, examples=["강남 행복주택"])
    area_sqm: Decimal = Field(gt=0, examples=["39.72"])
    recruitment_count: int = Field(gt=0, examples=[12])
    location: str = Field(min_length=1, max_length=50, examples=["강남구"])
    deposit: int = Field(ge=0, examples=[50000000])
    monthly_rent: int = Field(ge=0, examples=[350000])
    application_start_date: date
    application_end_date: date
    description: str = Field(min_length=1, examples=["전용면적 39.72㎡ 입주자를 모집합니다."])
    image_url: str | None = None
    source_url: str = Field(min_length=1, examples=["https://apply.lh.or.kr/"])


class ListingPublic(BaseModel):
    id: int
    title: str
    housing_name: str
    area_sqm: Decimal
    recruitment_count: int
    location: str
    deposit: int
    monthly_rent: int
    application_start_date: date
    application_end_date: date
    description: str
    image_url: str | None = None
    source_url: str
    created_at: datetime
