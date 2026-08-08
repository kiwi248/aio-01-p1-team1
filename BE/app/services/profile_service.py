# profile_service.py

from fastapi import HTTPException
from app.core.supabase_config import get_supabase
from app.schemas.profile_schema import ProfilePublic, ProfileUpdate


def profile_get(user_id: str) -> ProfilePublic | None:
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

    same_phone = (
        supabase.table("profiles")
        .select("id")
        .eq("phone", profile.phone)
        .neq("id", user_id)
        .execute()
    )

    if same_phone.data:
        raise HTTPException(
            status_code=409,
            detail="이미 사용 중인 휴대번호입니다.",
        )

    result = (
        supabase.table("profiles")
        .update(
            {
                "nickname": profile.nickname,
                "phone": profile.phone,
                "interests": profile.interests,
            }
        )
        .eq("id", user_id)
        .execute()
    )

    if not result.data:
        return None

    return ProfilePublic.model_validate(result.data[0])