import asyncio
from typing import Any, AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import MetaData, SQLModel

from app.api.setup import docs_basic_auth
from app.api.v3.routers.seller_products import seller_check
from app.core.config import settings as app_settings
from app.db import create_schema
from app.main import app
from app.models.fields_extensions_models import ProductBrandInDB, ProductColorInDB, ProductSizeInDB
from app.models.products_models import ProductCategoryInDB, ProductSubCategoryInDB
from app.mq.rabbitmq import RabbitMQ
from app.schemas.products_schemas import ProductCreate
from app.services.seller_products import Service
from tests import crud
from tests.mocks import SELLER_ID, MockSellerCheck, mock_s3_client, override_sessions
from tests.settings import settings as test_settings

from . import data as d

engine = create_async_engine(test_settings.sqlalchemy_database_url, future=True, poolclass=NullPool)
TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autocommit=False, autoflush=False)
metadata = MetaData(
    schema=app_settings.postgres_settings.schema_name,
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    },
)


@pytest.fixture(scope="session", autouse=True)
def event_loop() -> Generator[asyncio.AbstractEventLoop, Any, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def get_test_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn, TestingSessionLocal(bind=conn) as session:
        await create_schema(session)
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
        yield session


@pytest_asyncio.fixture
async def get_test_redis() -> AsyncGenerator[Redis, None]:
    async with Redis.from_url(url=test_settings.redis_dsn, encoding="utf-8") as redis:
        yield redis.client()
    await redis.flushall()


@pytest.fixture
def get_test_rabbit():
    yield RabbitMQ()


@pytest.fixture
def get_service_dependencies(get_test_session, get_test_redis, get_test_rabbit) -> Generator[tuple, Any, None]:
    yield get_test_session, get_test_redis, get_test_rabbit


@pytest_asyncio.fixture
async def async_client_unauthorized(get_test_session, get_test_redis) -> AsyncGenerator[AsyncClient, Any]:
    override_sessions(get_test_session, get_test_redis)
    async with AsyncClient(app=app, base_url=test_settings.test_service_dsn) as ac:
        yield ac


@pytest_asyncio.fixture
async def async_client_authorized(async_client_unauthorized) -> AsyncGenerator[AsyncClient, Any]:
    app.dependency_overrides[seller_check] = MockSellerCheck()
    app.dependency_overrides[docs_basic_auth] = lambda: None
    yield async_client_unauthorized
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def get_create_data() -> dict[str, Any]:
    return {
        "color": {"html_code": "AFAFAF", "name": "серый"},
        "size": {"group_name": "Взрослые размеры", "value": "34"},
        "brand": {"name": "Antonio Banderas"},
        "category": {"name": "Обувь", "name_slug": "footwear"},
        "subcategory": {"name": "Мужская обувь", "name_slug": "man_footwear", "category_id": NotImplementedError},
    }


@pytest_asyncio.fixture
async def get_color(get_test_session, get_create_data):
    return await crud.create(get_test_session, ProductColorInDB, **get_create_data["color"])


@pytest_asyncio.fixture
async def get_size(get_test_session, get_create_data):
    return await crud.create(get_test_session, ProductSizeInDB, **get_create_data["size"])


@pytest_asyncio.fixture
async def get_brand(get_test_session, get_create_data):
    return await crud.create(get_test_session, ProductBrandInDB, **get_create_data["brand"])


@pytest_asyncio.fixture
async def get_category(get_test_session, get_create_data):
    return await crud.create(get_test_session, ProductCategoryInDB, **get_create_data["category"])


@pytest_asyncio.fixture
async def get_subcategory(get_test_session, get_create_data, get_category):
    get_create_data["subcategory"]["category_id"] = get_category.id
    return await crud.create(get_test_session, ProductSubCategoryInDB, **get_create_data["subcategory"])


@pytest.fixture
def get_product_create_data(patch_s3, get_brand, get_color, get_size, get_subcategory) -> dict[str, Any]:
    return {
        "gender": "Женский",
        "barcode": 987654321,
        "status": "Новый",
        #
        "brand_id": get_brand.id,
        "color_id": get_color.id,
        "size_id": get_size.id,
        "subcategory_id": get_subcategory.id,
        #
        "country_of_manufacture": "КНР",
        "name": "Платье повседневное мини оверсайз",
        "vendor_code": "EPE0123",
        #
        "manually_filled_specification": d.MANUALLY_FILLED_SPEC,
        "pack": d.PACK,
        "price": d.PRICE,
        #
        "documents": [d.DOCUMENT],
        "images": [d.IMAGE],
    }


@pytest.fixture(scope="session")
def get_product_update_data() -> dict[str, Any]:
    return {
        "barcode": 987654321,
        "country_of_manufacture": "РФ",
        "gender": "Мужской",
        "name": "Джинсы",
        "vendor_code": "EPE9876",
    }


@pytest.fixture
def patch_s3(monkeypatch) -> None:
    monkeypatch.setattr("boto3.client", mock_s3_client)


@pytest.fixture
def get_service(get_service_dependencies):
    return Service(*get_service_dependencies)


@pytest_asyncio.fixture
async def get_product(get_service: Service, get_product_create_data):
    return await get_service.create_product(SELLER_ID, ProductCreate(**jsonable_encoder(get_product_create_data)))
