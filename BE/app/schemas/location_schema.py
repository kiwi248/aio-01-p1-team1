from pydantic import BaseModel, Field


class GeocodeResult(BaseModel):
    """주소를 좌표로 변환한 결과입니다."""

    address: str = Field(
        min_length=1,
        examples=["서울특별시 강남구 도곡로 464"],
    )
    latitude: float = Field(
        ge=-90,
        le=90,
        examples=[37.4966],
    )
    longitude: float = Field(
        ge=-180,
        le=180,
        examples=[127.0575],
    )