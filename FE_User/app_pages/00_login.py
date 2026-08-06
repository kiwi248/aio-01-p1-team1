# 00_login.py

import streamlit as st

from core.auth import is_logged_in, login


if is_logged_in():
    st.success("이미 로그인되어 있습니다.")
    st.stop()

st.title("로그인")

with st.form("login_form"):
    email = st.text_input("이메일")
    password = st.text_input("비밀번호", type="password")
    submitted = st.form_submit_button("로그인", type="primary")

if submitted:
    if not email.strip() or not password.strip():
        st.error("이메일과 비밀번호를 입력해 주세요.")
    else:
        with st.spinner("로그인 진행 중..."):
            login(email.strip(), password.strip())
