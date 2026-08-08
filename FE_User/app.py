"""유저용 Streamlit 멀티페이지 앱입니다."""

import streamlit as st

from core.auth import init_state, is_logged_in, logout


st.set_page_config(
    page_title="청약 정보 안내",
    page_icon="🏘️",
    layout="wide",
)

init_state()


home_page = st.Page("app_pages/02_home.py", title="홈", icon="🏠", default=True)
login_page = st.Page("app_pages/00_login.py", title="로그인", icon="🔐")
signup_page = st.Page("app_pages/01_signup.py", title="회원가입", icon="📝")
listings_page = st.Page("app_pages/03_listings.py", title="청약정보 조회", icon="📋")
mypage_page = st.Page("app_pages/04_mypage.py", title="My Page", icon="⭐")


if is_logged_in():
    pages = [home_page, listings_page, mypage_page]
else:
    pages = [home_page, login_page, signup_page, listings_page]

navigation = st.navigation(pages, position="hidden")

with st.sidebar:
    st.title("메뉴")
    st.page_link(home_page)
    st.page_link(listings_page)

    if is_logged_in():
        st.page_link(mypage_page)
        st.divider()
        st.caption(f"{st.session_state.email} 님")
        st.button("LOGOUT", on_click=logout, use_container_width=True)
    else:
        st.page_link(login_page)
        

navigation.run()


