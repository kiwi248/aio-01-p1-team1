# 02_home.py

import streamlit as st

from core.auth import is_logged_in


st.title("🏘️ 공공임대 및 분양 청약 통합 안내")

if is_logged_in():
    st.info(f"{st.session_state.email} 님, 환영합니다.")
    st.write("My Page에서 즐겨찾기한 청약정보를 확인할 수 있습니다.")
else:
    st.write("로그인하면 mypage에서 즐겨찾기를 관리할 수 있습니다.")

st.write("왼쪽 메뉴의 '청약정보 조회'에서 공고를 확인해 보세요.")
