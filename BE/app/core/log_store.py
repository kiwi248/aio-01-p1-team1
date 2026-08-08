# log_store.py
"""실시간 로그를 메모리에 저장하는 buffer와, 로그를 계속 만들어내는 시뮬레이터입니다.

DB를 쓰지 않고 collections.deque(maxlen=N)에 최근 로그만 들고 있습니다.
서버가 재시작되면 로그는 사라집니다. Render 무료 티어는 파일로 저장해도 재시작 시
초기화되므로, 이 데모에서는 메모리에 두는 것과 실질적인 차이가 없습니다.
"""

import random
import threading
import time
from collections import deque
from datetime import datetime, timezone

MAX_LOGS = 200
SIMULATE_INTERVAL_SECONDS = 2

LEVELS = ["info", "warning", "error"]
SCREENS = ["Listing", "Favorite", "Login", "Signup", "MyPage"]
MESSAGES = {
    "info": ["청약정보 조회", "즐겨찾기 등록", "로그인 성공", "닉네임 수정"],
    "warning": ["검색 조건 없이 전체 조회", "느린 응답 감지"],
    "error": ["비어 있는 이메일 입력", "청약정보 저장 실패", "인증 실패"],
}

# 여러 요청이 동시에 buffer를 건드릴 수 있으므로 lock으로 한 번에 하나씩만 접근합니다.
_log_buffer: deque[dict] = deque(maxlen=MAX_LOGS)
_lock = threading.Lock()


def add_log(level: str, screen: str, message: str, latency_ms: int) -> None:
    """로그 한 줄을 buffer에 추가합니다."""

    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "screen": screen,
        "message": message,
        "latency_ms": latency_ms,
    }
    with _lock:
        _log_buffer.append(entry)


def get_logs(level: str | None, limit: int) -> list[dict]:
    """buffer에서 최근 로그를 최신순으로 가져옵니다."""

    with _lock:
        logs = list(_log_buffer)

    if level and level != "all":
        logs = [log for log in logs if log["level"] == level]

    # deque는 오래된 순서로 쌓이므로, 최신 로그가 먼저 오도록 뒤집습니다.
    logs.reverse()
    return logs[:limit]


def _generate_random_log() -> None:
    """레벨에 맞는 화면·메시지를 무작위로 골라 로그 한 줄을 만듭니다."""

    # info를 더 자주, error는 드물게 만들어 실제 서비스와 비슷한 비율로 흉내 냅니다.
    level = random.choices(LEVELS, weights=[70, 20, 10])[0]
    screen = random.choice(SCREENS)
    message = random.choice(MESSAGES[level])
    latency_ms = random.randint(30, 300)

    add_log(level, screen, message, latency_ms)


def run_simulator() -> None:
    """일정 주기로 로그를 계속 만들어내는 루프입니다. 백그라운드 스레드에서 실행됩니다."""

    while True:
        _generate_random_log()
        time.sleep(SIMULATE_INTERVAL_SECONDS)


def start_simulator_thread() -> None:
    """시뮬레이터를 데몬 스레드로 시작합니다.

    daemon=True로 만들어야 FastAPI 서버가 종료될 때 이 스레드도 함께 끝납니다.
    """

    thread = threading.Thread(target=run_simulator, daemon=True)
    thread.start()
