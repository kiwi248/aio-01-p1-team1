# 01_home.py

import streamlit as st

from core.auth import is_logged_in


st.title("🛠️ 관리자 홈")

if is_logged_in():
    st.info(f"{st.session_state.admin_username} 님, 환영합니다.")
    st.write("왼쪽 메뉴에서 원하는 기능을 선택하세요.")
else:
    st.warning("왼쪽 메뉴에서 로그인해 주세요.")
