from typing import Any

from core.api_client import request


def get_listings():
    return request("GET", "/listings/getall")


def search_listings(params: dict[str, Any]):
    return request("GET", "/listings/search", params=params)


def get_listing(listing_id: int):
    return request("GET", f"/listings/get/{listing_id}")
