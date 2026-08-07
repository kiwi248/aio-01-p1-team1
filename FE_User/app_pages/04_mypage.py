# 04_mypage.py

from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st

from clients.favorite_client import delete_favorite, get_mypage_favorites
from clients.profile_client import get_profile, update_profile
from core.api_client import BackendAPIError
from core.auth import is_logged_in


def is_expired_listing(deadline: str | None) -> bool:
    if deadline is None:
        return False

    today = datetime.now(ZoneInfo("Asia/Seoul")).date()
    return date.fromisoformat(deadline) < today


st.title("My Page")

if not is_logged_in():
    st.warning("로그인이 필요합니다.")
    st.stop()

if message := st.session_state.pop("mypage_message", None):
    st.success(message)

try:
    profile_response = get_profile(st.session_state.user_id)
    profile = profile_response.get("data") or {}

    st.subheader("프로필")
    with st.form("profile_form"):
        nickname = st.text_input("닉네임", value=profile.get("nickname") or "")
        profile_submitted = st.form_submit_button("닉네임 수정")

    if profile_submitted:
        if not nickname.strip():
            st.warning("닉네임을 입력해 주세요.")
        else:
            result = update_profile(st.session_state.user_id, nickname.strip())
            st.session_state.mypage_message = result.get("message", "닉네임을 수정했습니다.")
            st.rerun()

    st.divider()
    st.subheader("즐겨찾기한 청약정보")

    favorites_response = get_mypage_favorites(st.session_state.user_id)
    favorites = favorites_response.get("data") or []

    if not favorites:
        st.info("즐겨찾기한 청약정보가 없습니다.")
    else:
        st.caption(f"총 {len(favorites)}건")

        for favorite in favorites:
            listing = favorite.get("listing") or {}
            title = listing.get("title") or "제목 없음"
            listing_info = (
                f"대상: {listing.get('type') or '-'}  |  "
                f"위치: {listing.get('location') or '-'}  |  "
                f"금액: {int(listing.get('price') or 0):,}원"
            )
            expired = is_expired_listing(listing.get("deadline"))

            with st.container(border=True):
                if expired:
                    st.caption(f"마감 · {title}")
                    st.caption(listing_info)
                else:
                    st.write(f"**{title}**")
                    st.write(listing_info)

                if st.button(
                    "즐겨찾기 삭제",
                    key=f"favorite-delete-{favorite['listing_id']}",
                ):
                    result = delete_favorite(st.session_state.user_id, favorite["listing_id"])
                    st.session_state.mypage_message = result.get(
                        "message", "즐겨찾기를 삭제했습니다."
                    )
                    st.rerun()
except BackendAPIError as error:
    st.error(str(error))
