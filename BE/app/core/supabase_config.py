"""Supabase 연결을 만드는 공통 helper입니다.

라우터 -> 서비스 어디서든 get_supabase()만 호출하면 Supabase client를 얻습니다.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

# 이 파일은 app/core/supabase_config.py에 있습니다.
# parents[2]는 프로젝트 루트(C:\aio-01-p1-team1)입니다.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"


def get_required_env(name: str) -> str:
    """필수 환경 변수를 읽고, 비어 있으면 오류를 냅니다."""

    value = os.getenv(name, "").strip()

    if not value:
        raise RuntimeError(f"{name} 값이 없습니다. {ENV_PATH} 파일을 확인하세요.")

    if value.startswith(("your-", "https://your-")):
        raise RuntimeError(f"{name} 값이 예시 값입니다. Supabase Dashboard에서 실제 값을 복사해 넣어 주세요.")

    return value


# 요청마다 client를 새로 만들면 TLS 연결도 매번 새로 맺어야 해서 느립니다.
# 프로세스 안에서 하나만 만들어 재사용합니다.
_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Supabase client를 생성하거나, 이미 만든 client를 재사용합니다.

    서버 코드에서 사용하므로 service role key를 사용합니다.
    service role key는 강한 권한을 가지므로 화면 코드나 GitHub에 노출하면 안 됩니다.
    """

    global _supabase_client

    if _supabase_client is None:
        load_dotenv(ENV_PATH)

        url = get_required_env("SUPABASE_URL")
        service_role_key = get_required_env("SUPABASE_SERVICE_ROLE_KEY")

        _supabase_client = create_client(url, service_role_key)

    return _supabase_client
