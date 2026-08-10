"""로그인 사용자를 위한 AI 채팅 상담 화면입니다."""

import streamlit as st

from clients.chat_client import (
    ChatAPIError,
    get_chat_profile,
    get_chat_summaries,
    save_chat_summary,
    send_chat_message,
)
from core.auth import is_logged_in


MESSAGE_KEY = "ai_chat_messages"
OWNER_KEY = "ai_chat_owner_id"
NICKNAME_KEY = "ai_chat_nickname"
END_CONFIRM_KEY = "ai_chat_end_confirm"
FLASH_KEY = "ai_chat_flash"
ERROR_KEY = "ai_chat_error"


def clear_current_chat() -> None:
    st.session_state[MESSAGE_KEY] = []
    st.session_state[END_CONFIRM_KEY] = False


def initialize_chat_state() -> None:
    current_user_id = st.session_state.user_id
    if st.session_state.get(OWNER_KEY) != current_user_id:
        st.session_state[OWNER_KEY] = current_user_id
        st.session_state[MESSAGE_KEY] = []
        st.session_state[NICKNAME_KEY] = "회원"
        st.session_state[END_CONFIRM_KEY] = False
    else:
        st.session_state.setdefault(MESSAGE_KEY, [])
        st.session_state.setdefault(NICKNAME_KEY, "회원")
        st.session_state.setdefault(END_CONFIRM_KEY, False)


def load_nickname() -> None:
    if st.session_state.get(NICKNAME_KEY) != "회원":
        return
    response = get_chat_profile(st.session_state.access_token)
    profile = response.get("data") or {}
    st.session_state[NICKNAME_KEY] = profile.get("nickname") or "회원"


def show_saved_summaries() -> None:
    st.subheader("저장된 상담")
    try:
        response = get_chat_summaries(st.session_state.access_token)
        summaries = response.get("data") or []
    except ChatAPIError as error:
        st.warning(str(error))
        return

    if not summaries:
        st.caption("저장된 상담 요약이 없습니다. 현재 테스트에서는 백엔드 메모리에만 보관됩니다.")
        return

    for item in summaries:
        created_at = str(item.get("created_at") or "").replace("T", " ")[:19]
        title = item.get("title") or "제목 없는 상담"
        with st.expander(f"{title} · {created_at}"):
            st.write(item.get("summary") or "요약 내용이 없습니다.")
            st.caption(
                f"메시지 {item.get('message_count', 0)}개 · model={item.get('model', '-') }"
            )


st.title("🤖 AI 채팅 상담")

if not is_logged_in():
    st.warning("AI 채팅 상담을 이용하려면 로그인이 필요합니다.")
    st.stop()

if not st.session_state.access_token:
    st.warning("로그인 토큰을 확인할 수 없습니다. 다시 로그인해 주세요.")
    st.stop()

initialize_chat_state()

try:
    load_nickname()
except ChatAPIError as error:
    st.warning(f"닉네임을 불러오지 못했습니다: {error}")

if flash_message := st.session_state.pop(FLASH_KEY, None):
    st.success(flash_message)
if error_message := st.session_state.pop(ERROR_KEY, None):
    st.error(error_message)

st.subheader(f"{st.session_state[NICKNAME_KEY]}님, 무엇을 도와드릴까요?")
st.caption("현재 대화는 이 화면에 임시 보관됩니다. 대화 저장 시 현재는 로컬 요약 미리보기로만 저장됩니다.")

show_saved_summaries()
st.divider()

for chat_message in st.session_state[MESSAGE_KEY]:
    with st.chat_message(chat_message["role"]):
        st.write(chat_message["content"])

prompt = st.chat_input("상담 질문을 입력하세요")
if prompt:
    history = list(st.session_state[MESSAGE_KEY])
    st.session_state[MESSAGE_KEY].append({"role": "user", "content": prompt})

    try:
        with st.spinner("AI 상담 답변을 생성하고 있습니다..."):
            response = send_chat_message(
                question=prompt,
                messages=history,
                access_token=st.session_state.access_token,
            )
        data = response.get("data") or {}
        st.session_state[MESSAGE_KEY].append(
            {"role": "assistant", "content": data.get("answer") or "답변이 비어 있습니다."}
        )
    except ChatAPIError as error:
        st.session_state[ERROR_KEY] = str(error)
    st.rerun()

end_col, save_col = st.columns(2)

with end_col:
    if st.button("대화 종료", use_container_width=True):
        st.session_state[END_CONFIRM_KEY] = True

with save_col:
    save_clicked = st.button(
        "대화 저장",
        type="primary",
        use_container_width=True,
        disabled=len(st.session_state[MESSAGE_KEY]) < 2,
    )

if st.session_state[END_CONFIRM_KEY]:
    st.warning("현재 상담 내용을 모두 삭제하시겠습니까? 저장하지 않은 대화는 복구할 수 없습니다.")
    cancel_col, confirm_col = st.columns(2)
    with cancel_col:
        if st.button("취소", use_container_width=True):
            st.session_state[END_CONFIRM_KEY] = False
            st.rerun()
    with confirm_col:
        if st.button("종료하기", type="primary", use_container_width=True):
            clear_current_chat()
            st.rerun()

if save_clicked:
    try:
        with st.spinner("상담 내용을 핵심만 요약하고 있습니다..."):
            response = save_chat_summary(
                st.session_state[MESSAGE_KEY],
                st.session_state.access_token,
            )
        clear_current_chat()
        st.session_state[FLASH_KEY] = response.get(
            "message", "상담 요약 미리보기를 저장했습니다."
        )
        st.rerun()
    except ChatAPIError as error:
        st.error(str(error))
