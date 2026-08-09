# image_action.py
"""공고를 수정할 때 이미지를 어떻게 할지 정하는 함수입니다.

수정 화면에는 이미지 입력이 두 개 있습니다.
  - 새 이미지 파일 고르기
  - 기존 이미지 삭제 선택

이 둘을 조합하면 뜻이 네 가지가 되므로, 화면 코드에서 조건문을 흩어 놓지 않고
여기서 한 번에 정합니다. Streamlit에 기대지 않는 순수 함수라 테스트하기 쉽습니다.
"""

# 저장할 때 이미지를 어떻게 할지 나타내는 값입니다.
KEEP = "keep"        # 기존 이미지를 그대로 둡니다.
REPLACE = "replace"  # 새 이미지로 바꿉니다.
REMOVE = "remove"    # 이미지를 없앱니다.
CONFLICT = "conflict"  # 새 이미지와 삭제를 함께 골랐습니다. 저장하지 않습니다.


def decide_image_action(has_new_image: bool, remove_selected: bool) -> str:
    """새 이미지 여부와 삭제 선택으로 저장할 때의 동작을 정합니다."""

    if has_new_image and remove_selected:
        # 조용히 한쪽을 무시하면 관리자가 결과를 예측할 수 없으므로 저장을 막습니다.
        return CONFLICT

    if has_new_image:
        return REPLACE

    if remove_selected:
        return REMOVE

    return KEEP


def build_image_fields(action: str) -> dict[str, str]:
    """수정 요청에 함께 보낼 이미지 관련 값을 만듭니다.

    파일 자체는 따로 보내고, 여기서는 "지워 달라"는 뜻만 담습니다.
    폼으로 보내므로 참/거짓을 문자열로 적습니다.
    """

    return {"remove_image": "true" if action == REMOVE else "false"}
