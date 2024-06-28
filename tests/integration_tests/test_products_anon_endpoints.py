import json
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
async def test__get_all__returns_empty_list(
    async_client_unauthorized: AsyncClient,
    view_name: str,
    expected: dict[str, Any],
    is_cache_empty,
    get_cache,
) -> None:
    assert await is_cache_empty()
    response_json = await request_get(async_client_unauthorized, view_name)
    assert response_json == []
    assert not await is_cache_empty()
    _ = await get_cache()
    cache = json.loads(_[0])
    assert cache == [], cache


@parametrize_get_all
async def test__get_all__returns_obj_list(
    async_client_unauthorized: AsyncClient,
    view_name: str,
    expected: dict[str, Any],
    get_product: ProductInDB,
) -> None:
    response_json = await request_get(async_client_unauthorized, view_name)
    compare(response_json, [expected])


async def test_get_product_by_name_slug_returns_not_found(async_client_unauthorized: AsyncClient) -> None:
    response_json = await request_get(
        async_client_unauthorized,
        view_name="product:get_product_by_name_slug",
        status_code=status.HTTP_404_NOT_FOUND,
        product_slug="test_slug",
    )
    assert response_json == {"detail": "Not Found"}


async def test__get_product_by_name_slug__returns_obj(
    async_client_unauthorized: AsyncClient,
    get_product: ProductInDB,
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
async def test__post__returns_empty_list(
    async_client_unauthorized: AsyncClient,
    view_name: str,
) -> None:
    response_json = await request_post(async_client_unauthorized, view_name, [UUID_ID])
    assert response_json == []


@parametrize_post
async def test__post__returns_objs_list(
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
    compare(response_json, [expected])
