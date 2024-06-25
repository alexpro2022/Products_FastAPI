import asyncio
from typing import Any, AsyncGenerator
from uuid import UUID

from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fields_extensions_models import ProductBrandInDB, ProductColorInDB, ProductSizeInDB
from app.models.products_models import ProductCategoryInDB, ProductInDB, ProductSubCategoryInDB
from app.services.seller_products import Service
from tests.mocks import SELLER_ID
from tests.utils import check_obj, is_base64, is_db_populated

from . import data as d
from .fixtures import RabbitMQ


async def test_provided_loop_is_running_loop(event_loop: asyncio.AbstractEventLoop) -> None:
    assert event_loop is asyncio.get_running_loop()


def test_get_session_fixture(get_test_session: AsyncSession) -> None:
    assert isinstance(get_test_session, AsyncSession)


async def test_get_redis_fixture(get_test_redis: Redis) -> None:
    assert isinstance(get_test_redis, Redis)
    assert await get_test_redis.get("key") is None
    for value in ("str", 1, 2.2):
        assert await get_test_redis.set("key", value)
        cache = await get_test_redis.get("key")
        assert cache.decode("utf-8") == str(value)
    assert await get_test_redis.delete("key")
    assert await get_test_redis.get("key") is None


def test_get_rabbit(get_test_rabbit: RabbitMQ) -> None:
    assert isinstance(get_test_rabbit, RabbitMQ)


def test_get_service_depenedencies_fixture(get_service_dependencies) -> None:
    session, cache, rabbit = get_service_dependencies
    assert isinstance(session, AsyncSession)
    assert isinstance(cache, Redis)
    assert isinstance(rabbit, RabbitMQ)


def test_async_client_unauthorized_fixture(async_client_unauthorized: AsyncGenerator[AsyncClient, Any]) -> None:
    assert isinstance(async_client_unauthorized, AsyncClient)


def test_async_client_authorized_fixture(async_client_authorized: AsyncGenerator[AsyncClient, Any]) -> None:
    assert isinstance(async_client_authorized, AsyncClient)


async def test_get_color_fixture(get_color, get_test_session, get_create_data) -> None:
    await check_obj(get_color, ProductColorInDB, get_test_session, get_create_data["color"])


async def test_get_size_fixture(get_size, get_test_session, get_create_data) -> None:
    await check_obj(get_size, ProductSizeInDB, get_test_session, get_create_data["size"])


async def test_get_brand_fixture(get_brand, get_test_session, get_create_data) -> None:
    await check_obj(get_brand, ProductBrandInDB, get_test_session, get_create_data["brand"])


async def test_get_category_fixture(get_category, get_test_session, get_create_data) -> None:
    await check_obj(get_category, ProductCategoryInDB, get_test_session, get_create_data["category"])


async def test_get_subcategory_fixture(get_subcategory, get_test_session, get_create_data, get_category) -> None:
    get_create_data["subcategory"]["category_id"] = str(get_category.id)
    await check_obj(get_subcategory, ProductSubCategoryInDB, get_test_session, get_create_data["subcategory"])


def test_get_product_create_data_fixture(get_product_create_data) -> None:
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


def test_get_product_update_data_fixture(get_product_update_data) -> None:
    pass


async def test_get_product_fixture(get_product: ProductInDB, get_test_session, get_product_create_data) -> None:
    assert get_product.seller_id == SELLER_ID
    await check_obj(get_product, ProductInDB, get_test_session, get_product_create_data)
    assert await is_db_populated(get_test_session)


def test_get_service_fixture(get_service) -> None:
    assert isinstance(get_service, Service)
