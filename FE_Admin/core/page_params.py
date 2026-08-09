# page_params.py
"""URL 주소창(query parameter)에 담는 화면 위치 값을 다루는 함수들입니다.

새로고침해도 보고 있던 목록 페이지와 수정 중인 공고가 유지되도록,
이 값들은 st.session_state가 아니라 URL에 둡니다.

여기에는 로그인 정보나 개인정보를 담지 않습니다.
화면 위치를 나타내는 페이지 번호와 공고 ID만 다룹니다.

Streamlit에 기대지 않는 순수 함수라 테스트하기 쉽습니다.
"""


def _first_value(raw: object) -> str | None:
    """주소에 같은 이름이 여러 번 들어와도 첫 값만 씁니다."""
    if isinstance(raw, (list, tuple)):
        return str(raw[0]) if raw else None
    if raw is None:
        return None
    return str(raw)


def parse_page(raw: object) -> int:
    """URL의 page 값을 페이지 번호로 바꿉니다.

    비어 있거나 숫자가 아니거나 1보다 작으면 1페이지로 봅니다.
    """
    value = _first_value(raw)
    if value is None:
        return 1

    try:
        page = int(value.strip())
    except ValueError:
        return 1

    return page if page >= 1 else 1


def parse_edit_id(raw: object) -> int | None:
    """URL의 edit_id 값을 공고 ID로 바꿉니다.

    비어 있거나 숫자가 아니거나 1보다 작으면 수정 모드가 아닌 것으로 봅니다.
    """
    value = _first_value(raw)
    if value is None:
        return None

    try:
        listing_id = int(value.strip())
    except ValueError:
        return None

    return listing_id if listing_id >= 1 else None


def build_params(page: int, edit_id: int | None = None) -> dict[str, str]:
    """주소창에 넣을 값을 만듭니다. 수정 중이 아니면 edit_id를 빼서 주소를 깔끔하게 둡니다."""
    params = {"page": str(max(1, page))}
    if edit_id is not None:
        params["edit_id"] = str(edit_id)
    return params
