"""관리자용 Streamlit 멀티페이지 앱입니다."""

import streamlit as st

from core.auth import init_state, is_logged_in, logout


st.set_page_config(
    page_title="관리자 페이지",
    page_icon="🛠️",
    layout="wide",
)

init_state()


home_page = st.Page("app_pages/01_home.py", title="홈", icon="🏠", default=True)
login_page = st.Page("app_pages/00_login.py", title="로그인", icon="🔐")
listing_create_page = st.Page("app_pages/02_listing_create.py", title="청약정보 등록", icon="📝")
listing_manage_page = st.Page("app_pages/03_listing_manage.py", title="청약정보 조회/삭제", icon="📋")
favorite_ranking_page = st.Page("app_pages/04_favorite_ranking.py", title="즐겨찾기 순위", icon="⭐")
favorite_detail_page = st.Page("app_pages/05_favorite_detail.py", title="즐겨찾기 상세", icon="🔍")
log_dashboard_page = st.Page("app_pages/06_log_dashboard.py", title="로그 대시보드", icon="📊")


if is_logged_in():
    pages = [
        home_page,
        listing_create_page,
        listing_manage_page,
        favorite_ranking_page,
        favorite_detail_page,
        log_dashboard_page,
    ]
else:
    pages = [home_page, login_page]

navigation = st.navigation(pages, position="hidden")

with st.sidebar:
    st.title("관리자 메뉴")
    st.page_link(home_page)

    if is_logged_in():
        st.page_link(listing_create_page)
        st.page_link(listing_manage_page)
        st.page_link(favorite_ranking_page)
        st.page_link(favorite_detail_page)
        st.page_link(log_dashboard_page)

        st.divider()
        st.caption(f"{st.session_state.admin_username} 님 로그인 중")
        st.button("LOGOUT", on_click=logout, use_container_width=True)
    else:
        st.page_link(login_page)

navigation.run()
