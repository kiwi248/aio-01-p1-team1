# log_schema.py
from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    time: str = Field(examples=["2026-08-07T09:10:12+00:00"])
    level: str = Field(examples=["info"])
    screen: str = Field(examples=["Listing"])
    message: str = Field(examples=["청약정보 조회"])
    latency_ms: int = Field(examples=[80])
