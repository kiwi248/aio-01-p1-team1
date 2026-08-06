from core.api_client import request


def get_profile(user_id: str):
    return request("GET", f"/profiles/{user_id}")


def update_profile(user_id: str, nickname: str):
    return request("PUT", f"/profiles/{user_id}", json={"nickname": nickname})
