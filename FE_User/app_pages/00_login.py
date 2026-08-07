# 00_login.py

import streamlit as st

from core.auth import is_logged_in, login


EMAIL_DOMAINS = [
    "naver.com",
    "gmail.com",
    "daum.net",
    "kakao.com",
    "직접 입력",
]


if is_logged_in():
    st.success("이미 로그인되어 있습니다.")
    st.stop()

st.title("로그인")
st.caption("가입할 때 사용한 이메일과 비밀번호를 입력해 주세요.")

email_col, domain_col = st.columns([2, 1])

with email_col:
    email_id = st.text_input(
        "이메일",
        placeholder="이메일 아이디",
    )

with domain_col:
    selected_domain = st.selectbox(
        "이메일 주소",
        EMAIL_DOMAINS,
    )

if selected_domain == "직접 입력":
    email_domain = email_domain = selected_domain
    
else:
    email_domain = selected_domain

password = st.text_input(
    "비밀번호",
    type="password",
    placeholder="비밀번호를 입력해 주세요.",
)

st.markdown(
    """
    <style>
    [data-testid="stMain"] a[data-testid="stPageLink-NavLink"] {
        background-color: var(--secondary-background-color, #f0f2f6);
        border-radius: 0.5rem;
        justify-content: center;
        min-height: 2.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

button_col1, button_col2 = st.columns(2)

with button_col1:
    login_clicked = st.button(
        "로그인",
        type="primary",
        use_container_width=True,
    )

with button_col2:
    st.page_link(
        "app_pages/01_signup.py",
        label="회원가입",
        use_container_width=True,
    )

if login_clicked:
    clean_email_id = email_id.strip()
    clean_domain = email_domain.strip()
    clean_password = password.strip()

    if not clean_email_id:
        st.error("이메일 아이디를 입력해 주세요.")
    elif not clean_domain:
        st.error("이메일 주소를 입력해 주세요.")
    elif "@" in clean_email_id:
        st.error("@ 앞부분만 입력해 주세요.")
    elif not clean_password:
        st.error("비밀번호를 입력해 주세요.")
    else:
        full_email = f"{clean_email_id}@{clean_domain}"

        with st.spinner("로그인 진행 중..."):
            login(full_email, clean_password)