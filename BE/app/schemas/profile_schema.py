
from datetime import datetime

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    nickname: str = Field(
        min_length=1,
        max_length=50,
        examples=["홍길동"],
    )
    phone: str = Field(
        pattern=r"^010-\d{4}-\d{4}$",
        examples=["010-1234-5678"],
    )
    interests: list[str] = Field(
        default_factory=list,
        examples=[["분양주택", "임대주택"]],
    )


class ProfilePublic(BaseModel):
    id: str = Field(
        examples=["b3f1c2a0-1234-4a5b-9c3d-abcdef123456"]
    )
    nickname: str | None = None
    phone: str | None = None
    interests: list[str] = Field(default_factory=list)
    created_at: datetime