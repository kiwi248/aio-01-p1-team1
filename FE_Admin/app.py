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
log_history_page = st.Page("app_pages/07_log_history.py", title="로그 이력 조회", icon="🗂️")


# 페이지는 로그인 여부와 상관없이 모두 등록합니다.
# 로그인 상태에 따라 목록을 바꾸면, 브라우저를 새로고침했을 때
# st.session_state가 비어 있어 지금 보고 있던 주소가 목록에서 사라지고
# "Page not found"가 뜹니다.
# 등록은 항상 하되, 아래에서 로그인 여부를 검사합니다.
pages = [
    home_page,
    login_page,
    listing_create_page,
    listing_manage_page,
    favorite_ranking_page,
    favorite_detail_page,
    log_dashboard_page,
    log_history_page,
]

navigation = st.navigation(pages, position="hidden")

# 로그인 없이 볼 수 있는 페이지입니다. 나머지는 모두 보호 페이지입니다.
public_url_paths = {home_page.url_path, login_page.url_path}

# 보호 페이지에 로그인 없이 들어오면 오류 화면 대신 로그인 화면으로 보냅니다.
# 주소를 직접 입력해도 여기서 걸리므로 관리자 기능에 접근할 수 없습니다.
if navigation.url_path not in public_url_paths and not is_logged_in():
    st.switch_page("app_pages/00_login.py")

with st.sidebar:
    st.title("관리자 메뉴")
    st.page_link(home_page)

    if is_logged_in():
        st.page_link(listing_create_page)
        st.page_link(listing_manage_page)
        st.page_link(favorite_ranking_page)
        st.page_link(favorite_detail_page)
        st.page_link(log_dashboard_page)
        st.page_link(log_history_page)

        st.divider()
        st.caption(f"{st.session_state.admin_username} 님 로그인 중")
        st.button("LOGOUT", on_click=logout, use_container_width=True)
    else:
        st.page_link(login_page)

navigation.run()
