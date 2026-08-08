from typing import Any

from core.api_client import request


def create_listing(listing: dict[str, Any]):
    return request("POST", "/admin/listings/create", json=listing)


def upload_listing_image(image: Any):
    files = {
        "image": (
            image.name,
            image.getvalue(),
            image.type or "application/octet-stream",
        )
    }
    return request("POST", "/admin/listings/images", files=files)


def get_listings():
    return request("GET", "/listings/getall")


def get_listing(listing_id: int):
    return request("GET", f"/listings/get/{listing_id}")


def search_listings(params: dict[str, Any]):
    return request("GET", "/listings/search", params=params)


def update_listing(listing_id: int, listing: dict[str, Any], image: Any = None):
    # 이미지가 함께 갈 수 있어 등록과 달리 multipart 방식으로 보냅니다.
    files = None
    if image is not None:
        files = {
            "image": (
                image.name,
                image.getvalue(),
                image.type or "application/octet-stream",
            )
        }
    return request(
        "PUT",
        f"/admin/listings/update/{listing_id}",
        data=listing,
        files=files,
    )


def delete_listing(listing_id: int):
    return request("DELETE", f"/admin/listings/delete/{listing_id}")
