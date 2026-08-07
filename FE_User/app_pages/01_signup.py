# 01_signup.py

import streamlit as st

from core.auth import is_logged_in, sign_up


EMAIL_DOMAINS = [
    "naver.com",
    "gmail.com",
    "daum.net",
    "kakao.com",
    "직접 입력",
]


def initialize_signup_state():
    """회원가입 화면에서 사용할 약관 동의 상태를 준비합니다."""
    st.session_state.setdefault("signup_agree_all", False)
    st.session_state.setdefault("signup_agree_terms", False)
    st.session_state.setdefault("signup_agree_privacy", False)


def change_all_agreements():
    """전체 동의 상태를 두 개의 필수 약관에 반영합니다."""
    agree_all = st.session_state.signup_agree_all

    st.session_state.signup_agree_terms = agree_all
    st.session_state.signup_agree_privacy = agree_all


def update_all_agreement():
    """개별 약관 상태에 따라 전체 동의 상태를 변경합니다."""
    st.session_state.signup_agree_all = (
        st.session_state.signup_agree_terms
        and st.session_state.signup_agree_privacy
    )


initialize_signup_state()


if is_logged_in():
    st.success("이미 로그인되어 있습니다.")
    st.stop()


st.title("회원가입")
st.caption("필수 약관에 동의한 후 회원 정보를 입력해 주세요.")

# 진행 상태를 표시합니다.
required_agreement_count = sum(
    [
        st.session_state.signup_agree_terms,
        st.session_state.signup_agree_privacy,
    ]
)

if required_agreement_count < 2:
    st.progress(50, text="1단계: 약관 동의")
else:
    st.progress(100, text="2단계: 회원 정보 입력")


st.subheader("1. 약관 동의")
st.info("회원가입을 진행하려면 아래 필수 약관에 모두 동의해야 합니다.")

st.checkbox(
    "약관 전체 동의",
    key="signup_agree_all",
    on_change=change_all_agreements,
)

st.divider()

with st.expander("필수 · 회원가입 약관", expanded=True):
    st.write(
        """
        본 서비스의 회원으로 가입하면 서비스 이용 규칙을 준수해야 합니다.

        - 다른 사람의 개인정보를 도용할 수 없습니다.
        - 서비스를 부정한 목적으로 이용할 수 없습니다.
        - 회원 정보는 정확하게 입력해야 합니다.
        """
    )

    st.checkbox(
        "회원가입 약관에 동의합니다.",
        key="signup_agree_terms",
        on_change=update_all_agreement,
    )

with st.expander("필수 · 개인정보 수집 및 이용", expanded=True):
    st.write(
        """
        회원가입과 서비스 제공을 위해 다음 개인정보를 수집합니다.

        - 수집 항목: 이메일, 닉네임
        - 이용 목적: 사용자 확인 및 서비스 제공
        - 보유 기간: 회원 탈퇴 시까지

        필수 개인정보 수집에 동의하지 않으면 회원가입을 진행할 수 없습니다.
        """
    )

    st.checkbox(
        "개인정보 수집 및 이용에 동의합니다.",
        key="signup_agree_privacy",
        on_change=update_all_agreement,
    )


st.divider()
st.subheader("2. 회원 정보 입력")

email_col, domain_col = st.columns([2, 1])

with email_col:
    email_id = st.text_input(
        "이메일",
        placeholder="이메일 아이디",
        key="signup_email_id",
    )

with domain_col:
    selected_domain = st.selectbox(
        "이메일 주소",
        EMAIL_DOMAINS,
        key="signup_selected_domain",
    )

    if selected_domain == "직접 입력":
        email_domain = st.text_input(
            "도메인 직접 입력",
            placeholder="example.com",
            key="signup_custom_domain",
            label_visibility="collapsed",
        )
    else:
        email_domain = selected_domain

password = st.text_input(
    "비밀번호",
    type="password",
    placeholder="6자 이상 입력해 주세요.",
    key="signup_password",
)

password_confirm = st.text_input(
    "비밀번호 확인",
    type="password",
    placeholder="비밀번호를 다시 입력해 주세요.",
    key="signup_password_confirm",
)

nickname = st.text_input(
    "닉네임",
    placeholder="사용할 닉네임을 입력해 주세요.",
    key="signup_nickname",
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
    submitted = st.button(
        "회원가입",
        type="primary",
        use_container_width=True,
    )

with button_col2:
    st.page_link(
        "app_pages/00_login.py",
        label="로그인으로 돌아가기",
        use_container_width=True,
    )


if submitted:
    clean_email_id = email_id.strip()
    clean_domain = email_domain.strip()
    clean_nickname = nickname.strip()

    if not st.session_state.signup_agree_terms:
        st.error("회원가입 약관에 동의해 주세요.")
    elif not st.session_state.signup_agree_privacy:
        st.error("개인정보 수집 및 이용에 동의해 주세요.")
    elif not clean_email_id:
        st.error("이메일 아이디를 입력해 주세요.")
    elif "@" in clean_email_id:
        st.error("이메일 아이디에는 @ 앞부분만 입력해 주세요.")
    elif not clean_domain:
        st.error("이메일 주소를 입력해 주세요.")
    elif "@" in clean_domain:
        st.error("이메일 주소에는 @를 제외하고 입력해 주세요.")
    elif not password:
        st.error("비밀번호를 입력해 주세요.")
    elif len(password) < 6:
        st.error("비밀번호는 6자 이상 입력해 주세요.")
    elif password != password_confirm:
        st.error("비밀번호가 일치하지 않습니다.")
    elif not clean_nickname:
        st.error("닉네임을 입력해 주세요.")
    else:
        full_email = f"{clean_email_id}@{clean_domain}"

        with st.spinner("회원가입 진행 중..."):
            sign_up(
                full_email,
                password,
                clean_nickname,
            )