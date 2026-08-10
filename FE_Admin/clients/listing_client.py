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


def get_listings_page(page: int, page_size: int = 10, sort: str | None = None):
    # 전체를 받아 오지 않고 필요한 페이지만 가져옵니다.
    # 정렬도 백엔드에 맡깁니다. 받은 10건만 다시 늘어놓으면
    # 전체 기준의 순서가 아니라 그 페이지 안에서만 뒤바뀌기 때문입니다.
    params = {"page": page, "page_size": page_size}
    if sort:
        params["sort"] = sort
    return request("GET", "/listings/page", params=params)


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


def delete_listing_image(listing_id: int):
    # 공고 id만 보냅니다. 수정 폼에 입력해 둔 값은 함께 보내지 않습니다.
    return request("DELETE", f"/admin/listings/{listing_id}/image")
