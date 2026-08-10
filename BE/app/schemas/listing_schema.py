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
    # 자치구만으로는 어느 동네인지 알기 어려워 도로명 주소를 따로 받습니다. 선택 입력입니다.
    detail_address: str | None = Field(
        default=None, max_length=255, examples=["서울 강남구 도곡로 464"]
    )
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
    detail_address: str | None = None
    deposit: int
    monthly_rent: int
    application_start_date: date
    application_end_date: date
    description: str
    image_url: str | None = None
    source_url: str
    created_at: datetime


class ListingPage(BaseModel):
    """목록을 페이지로 나눠 보낼 때 쓰는 응답입니다.

    화면이 전체 페이지 수를 계산할 수 있도록 개수 정보를 함께 담습니다.
    """

    items: list[ListingPublic]
    page: int
    page_size: int
    total_count: int
    total_pages: int
