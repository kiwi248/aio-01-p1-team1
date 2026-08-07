"""공통 로그인 상태와 Supabase Auth 인증 동작을 관리합니다."""

import streamlit as st
from supabase import AuthApiError

from core.supabase_client import get_supabase


def init_state(
    stored_loginout: str = "logout",
    stored_user_id: str = "",
    stored_email: str = "",
) -> None:
    st.session_state.setdefault("loginout", stored_loginout)
    st.session_state.setdefault("user_id", stored_user_id)
    st.session_state.setdefault("email", stored_email)


def sign_up(
    email: str,
    password: str,
    nickname: str,
    phone: str,
    birth_date: str,
    interests: list[str],
) -> None:
    supabase = get_supabase()

    try:
        result = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "nickname": nickname,
                        "phone": phone,
                        "birth_date": birth_date,
                        "interests": interests,
                    }
                },
            }
        )
    except AuthApiError as error:
        st.error(f"회원가입에 실패했습니다: {error.message}")
        return

    if result.session is None:
        st.success("회원가입이 완료되었습니다. 이메일 인증 후 로그인해 주세요.")
    else:
        st.success("회원가입이 완료되었습니다. 로그인해 주세요.")


def login(email: str, password: str) -> None:
    supabase = get_supabase()
    try:
        result = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except AuthApiError as error:
        st.error(f"로그인에 실패했습니다: {error.message}")
        return

    st.session_state.loginout = "login"
    st.session_state.user_id = result.user.id
    st.session_state.email = result.user.email or ""
    st.rerun()


def logout() -> None:
    st.session_state.loginout = "logout"
    st.session_state.user_id = ""
    st.session_state.email = ""


def is_logged_in() -> bool:
    return st.session_state.loginout == "login"
