# create_form.py
"""청약정보 등록 폼의 입력값을 다루는 함수들입니다.

비슷한 공고를 이어서 여러 건 넣는 일이 많아, 등록한 뒤에도 입력값을 지우지 않고
그대로 둡니다. 아예 새 공고를 넣을 때는 `입력 초기화` 버튼으로 한 번에 비웁니다.

Streamlit에 기대지 않는 함수만 두어 테스트하기 쉽습니다.
"""

# 등록 폼 입력칸의 이름입니다. 초기화할 때 이 이름들만 지웁니다.
CREATE_FORM_KEYS = (
    "create-title",
    "create-housing-name",
    "create-area-sqm",
    "create-recruitment-count",
    "create-location",
    "create-deposit",
    "create-monthly-rent",
    "create-start-date",
    "create-end-date",
    "create-description",
    "create-image",
    "create-source-url",
)


def reset_form_state(state) -> list[str]:
    """등록 폼 입력값을 지웁니다.

    지운 이름을 돌려줍니다. 값이 없던 이름은 그냥 넘어갑니다.
    등록 폼과 상관없는 값(로그인 정보 등)은 건드리지 않습니다.
    """

    cleared = []
    for key in CREATE_FORM_KEYS:
        if key in state:
            del state[key]
            cleared.append(key)

    return cleared
