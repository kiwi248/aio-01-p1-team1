# 01_signup.py

import streamlit as st

from core.auth import is_logged_in, sign_up


if is_logged_in():
    st.success("이미 로그인되어 있습니다.")
    st.stop()

st.title("회원가입")
st.caption("지금은 이메일로만 가입할 수 있습니다. (추후 Kakao, Google 로그인 추가 예정)")

with st.form("signup_form", clear_on_submit=True):
    email = st.text_input("이메일")
    password = st.text_input("비밀번호", type="password")
    password_confirm = st.text_input("비밀번호 확인", type="password")
    nickname = st.text_input("닉네임")
    submitted = st.form_submit_button("회원가입", type="primary")

if submitted:
    if not email.strip() or not password or not nickname.strip():
        st.warning("이메일, 비밀번호, 닉네임을 모두 입력해 주세요.")
    elif password != password_confirm:
        st.warning("비밀번호가 일치하지 않습니다.")
    else:
        with st.spinner("회원가입 진행 중..."):
            sign_up(email.strip(), password, nickname.strip())
