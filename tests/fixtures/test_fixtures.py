import asyncio
from typing import Any, AsyncGenerator
from uuid import UUID

import pytest
from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fields_extensions_models import ProductBrandInDB, ProductColorInDB, ProductSizeInDB
from app.models.products_models import ProductCategoryInDB, ProductInDB, ProductSubCategoryInDB
from app.services.seller_products import Service
from tests.mocks import SELLER_ID
from tests.utils import check_obj, is_base64, is_db_populated, to_json

from . import data as d
from .fixtures import RabbitMQ


async def test_provided_loop_is_running_loop(event_loop: asyncio.AbstractEventLoop) -> None:
    assert event_loop is asyncio.get_running_loop()


def test__get_session__fixture(get_test_session: AsyncSession) -> None:
    assert isinstance(get_test_session, AsyncSession)


async def test__get_redis__fixture(get_test_redis: Redis) -> None:
    assert isinstance(get_test_redis, Redis)
    assert await get_test_redis.get("key") is None
    for value in ("str", 1, 2.2):
        assert await get_test_redis.set("key", value)
        assert await get_test_redis.get("key") == str(value).encode()
    assert await get_test_redis.delete("key")
    assert await get_test_redis.get("key") is None


@pytest.mark.parametrize(
    "decode, expected",
    (
        (True, ["2.2", '[1, 2.2, "str"]', '{"key": [1, 2.2, "str"]}', "1", "str"]),
        (False, [b"2.2", b'[1, 2.2, "str"]', b'{"key": [1, 2.2, "str"]}', b"1", b"str"]),
    ),
)
async def test__get_cache__fixture(get_cache, get_test_redis, decode: bool, expected: list[str | bytes]) -> None:
    test_data = (1, 2.2, "str")
    for idx, value in enumerate((*test_data, to_json({*test_data}), to_json({"key": test_data}))):
        assert await get_test_redis.set(f"{idx}", value)
    cache = await get_cache(decode=decode)
    assert set(cache) == set(expected)


async def test__is_cache_empty__fixture(is_cache_empty, get_test_redis: Redis):
    assert await is_cache_empty()
    assert await get_test_redis.set("key", "value")
    assert not await is_cache_empty()


def test__get_rabbit__fixture(get_test_rabbit: RabbitMQ) -> None:
    assert isinstance(get_test_rabbit, RabbitMQ)


def test__get_service_depenedencies__fixture(get_service_dependencies) -> None:
    session, cache, rabbit = get_service_dependencies
    assert isinstance(session, AsyncSession)
    assert isinstance(cache, Redis)
    assert isinstance(rabbit, RabbitMQ)


def test__async_client_unauthorized__fixture(async_client_unauthorized: AsyncGenerator[AsyncClient, Any]) -> None:
    assert isinstance(async_client_unauthorized, AsyncClient)


def test__async_client_authorized__fixture(async_client_authorized: AsyncGenerator[AsyncClient, Any]) -> None:
    assert isinstance(async_client_authorized, AsyncClient)


async def test__get_color__fixture(get_color, get_test_session, get_create_data) -> None:
    await check_obj(get_color, get_test_session, ProductColorInDB, get_create_data["color"])


async def test__get_size__fixture(get_size, get_test_session, get_create_data) -> None:
    await check_obj(get_size, get_test_session, ProductSizeInDB, get_create_data["size"])


async def test__get_brand__fixture(get_brand, get_test_session, get_create_data) -> None:
    await check_obj(get_brand, get_test_session, ProductBrandInDB, get_create_data["brand"])


async def test__get_category__fixture(get_category, get_test_session, get_create_data) -> None:
    await check_obj(get_category, get_test_session, ProductCategoryInDB, get_create_data["category"])


async def test__get_subcategory__fixture(get_subcategory, get_test_session, get_create_data, get_category) -> None:
    get_create_data["subcategory"]["category_id"] = str(get_category.id)
    await check_obj(get_subcategory, get_test_session, ProductSubCategoryInDB, get_create_data["subcategory"])


def test__get_product_create_data__fixture(get_product_create_data) -> None:
    expected_fields = (
        ("barcode", int),
        #
        ("brand_id", UUID),
        ("color_id", UUID),
        ("size_id", UUID),
        ("subcategory_id", UUID),
        #
        ("gender", str),
        ("status", str),
        ("country_of_manufacture", str),
        ("name", str),
        ("vendor_code", str),
        #
        ("manually_filled_specification", dict),
        ("pack", dict),
        ("price", dict),
        #
        ("documents", list),
        ("images", list),
    )
    assert isinstance(get_product_create_data, dict)
    assert len(get_product_create_data) == len(expected_fields)
    for key, value in expected_fields:
        assert isinstance(get_product_create_data[key], value)

    assert get_product_create_data["manually_filled_specification"] == d.MANUALLY_FILLED_SPEC
    assert get_product_create_data["pack"] == d.PACK
    assert get_product_create_data["price"] == d.PRICE

    for item in get_product_create_data["documents"]:
        is_base64(item["document"])
        assert item["name"] == "document_name"
    for item in get_product_create_data["images"]:
        is_base64(item["image"])
        assert item["order_num"] == 0


def test__get_product_update_data__fixture(get_product_update_data) -> None:
    pass


async def test__get_product__fixture(get_product: ProductInDB, get_test_session, get_product_create_data) -> None:
    assert get_product.seller_id == SELLER_ID
    await check_obj(get_product, get_test_session, ProductInDB, get_product_create_data)
    assert await is_db_populated(get_test_session)


def test__get_service__fixture(get_service) -> None:
    assert isinstance(get_service, Service)
