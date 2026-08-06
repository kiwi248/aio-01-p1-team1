# profile_service.py
from app.core.supabase_config import get_supabase
from app.schemas.profile_schema import ProfilePublic, ProfileUpdate


def profile_get(user_id: str) -> ProfilePublic | None:
    """ 회원가입/로그인은 Supabase Auth가 처리하고, profiles는 auth.users 생성 시
    트리거로 자동 생성됩니다. """
    supabase = get_supabase()
    result = (
        supabase.table("profiles")
        .select("*")
        .eq("id", user_id)
        .execute()
    )
    if not result.data:
        return None
    return ProfilePublic.model_validate(result.data[0])


def profile_update(user_id: str, profile: ProfileUpdate) -> ProfilePublic | None:
    supabase = get_supabase()
    result = (
        supabase.table("profiles")
        .update({"nickname": profile.nickname})
        .eq("id", user_id)
        .execute()
    )
    if not result.data:
        return None
    return ProfilePublic.model_validate(result.data[0])
