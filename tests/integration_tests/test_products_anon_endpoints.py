from typing import Any

import pytest
from fastapi import status
from httpx import AsyncClient

from app.models.products_models import ProductInDB
from tests.mocks import UUID_ID
from tests.utils import compare, request_get, request_post

from . import data as d

parametrize_get_all = pytest.mark.parametrize(
    "view_name, expected",
    (
        ("size:get_all_sizes", d.SIZE_RESPONSE),
        ("color:get_all_colors", d.COLOR_RESPONSE),
        ("brand:get_all_brands", d.BRAND_RESPONSE),
        ("category:get_all_categories_and_subcategories", d.CATEGORIES_RESPONSE),
    ),
)


@parametrize_get_all
async def test_get_all_returns_empty_list(
    async_client_unauthorized: AsyncClient,
    view_name: str,
    expected: dict[str, Any],
) -> None:
    response_json = await request_get(async_client_unauthorized, view_name)
    expected = []
    assert response_json == expected


@parametrize_get_all
async def test_get_all_returns_obj_list(
    async_client_unauthorized: AsyncClient,
    view_name: str,
    expected: dict[str, Any],
    get_product: ProductInDB,
) -> None:
    response_json = await request_get(async_client_unauthorized, view_name)
    expected["id"] = response_json[0]["id"]
    assert response_json == [expected]


async def test_get_product_by_name_slug_returns_not_found(async_client_unauthorized: AsyncClient) -> None:
    response_json = await request_get(
        async_client_unauthorized,
        view_name="product:get_product_by_name_slug",
        status_code=status.HTTP_404_NOT_FOUND,
        product_slug="test_slug",
    )
    expected = {"detail": "Not Found"}
    assert response_json == expected


async def test_get_product_by_name_slug_returns_obj(
    async_client_unauthorized: AsyncClient, get_product: ProductInDB
) -> None:
    response_json = await request_get(
        async_client_unauthorized,
        view_name="product:get_product_by_name_slug",
        product_slug=get_product.name_slug,
    )
    compare(response_json, get_product)


parametrize_post = pytest.mark.parametrize(
    "view_name",
    (
        "product:get_by_ids",
        "product:get_products_prices",
    ),
)


@parametrize_post
async def test_post_returns_empty_list(
    async_client_unauthorized: AsyncClient,
    view_name: str,
) -> None:
    response_json = await request_post(async_client_unauthorized, view_name, [UUID_ID])
    expected = []
    assert response_json == expected


@parametrize_post
async def test_post_returns_objs_list(
    async_client_unauthorized: AsyncClient,
    view_name: str,
    get_product: ProductInDB,
) -> None:
    response_json = await request_post(async_client_unauthorized, view_name, [get_product.id])
    expected = (
        get_product
        if view_name == "product:get_by_ids"
        else {"price_without_discount": 119.99, "price_with_discount": 99.99, "vat": "20%"}
    )
    for item in response_json:
        compare(item, expected)
