# log_service.py
from app.core.log_store import get_logs
from app.schemas.log_schema import LogEntry


def log_list(level: str | None, limit: int) -> list[LogEntry]:
    """메모리 buffer에서 로그를 조회해 응답 모델로 바꿉니다."""

    logs = get_logs(level=level, limit=limit)
    return [LogEntry.model_validate(log) for log in logs]
