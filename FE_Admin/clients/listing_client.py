from typing import Any

from core.api_client import request


def create_listing(listing: dict[str, Any]):
    return request("POST", "/admin/listings/create", json=listing)


def get_listings():
    return request("GET", "/listings/getall")


def search_listings(params: dict[str, Any]):
    return request("GET", "/listings/search", params=params)


def delete_listing(listing_id: int):
    return request("DELETE", f"/admin/listings/delete/{listing_id}")
