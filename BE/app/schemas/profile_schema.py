# profile_schema.py
from datetime import datetime

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    nickname: str = Field(min_length=1, max_length=50, examples=["홍길동"])


class ProfilePublic(BaseModel):
    id: str = Field(examples=["b3f1c2a0-1234-4a5b-9c3d-abcdef123456"])
    nickname: str | None = None
    created_at: datetime
