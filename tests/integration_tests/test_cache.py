import asyncio
import json
from typing import Any
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.models import products_models as pm
from app.models.fields_extensions_models import ProductStatus, ProductStatusForChange
from tests import crud, mocks
from tests.utils import ModelType, compare, request_get, request_patch, request_post

from . import data as d
from .test_products_anon_endpoints import parametrize_post

REGEX = r"(.*, 'TEST_VALUE')"
EXCLUDE = ("created_at", "updated_at")
# exclude `created_at/updated_at` as different time formats in the cache and db (the value is the same)


# ================ TEST CACHE ================
@pytest.mark.parametrize(
    "view_name, expected, model",
    (
        ("size:get_all_sizes", d.SIZE_RESPONSE, pm.ProductSizeInDB),
        ("color:get_all_colors", d.COLOR_RESPONSE, pm.ProductColorInDB),
        ("brand:get_all_brands", d.BRAND_RESPONSE, pm.ProductBrandInDB),
        ("category:get_all_categories_and_subcategories", d.CATEGORIES_RESPONSE, pm.ProductCategoryInDB),
    ),
)
async def test__get_all__cache_scenario(
    async_client_unauthorized: AsyncClient,
    view_name: str,
    expected: dict[str, Any],
    model: ModelType,
    get_product: pm.ProductInDB,
    is_cache_empty,
    get_cache,
    get_test_session,
) -> None:
    def __():
        def _(item_id: UUID, item_field_name: str = "name"):
            return item_id, {item_field_name: "TEST_VALUE"}

        match model:
            case pm.ProductSizeInDB:
                return _(get_product.size_id, "value")
            case pm.ProductColorInDB:
                return _(get_product.color_id)
            case pm.ProductBrandInDB:
                return _(get_product.brand_id)
            case pm.ProductCategoryInDB:
                return _(get_product.subcategory.category_id)

    # Step 1: Verify the cache has been set up
    assert await is_cache_empty()
    original_response_json = await request_get(async_client_unauthorized, view_name)
    assert not await is_cache_empty()
    # Step 2: Verify the cache corresponds to expected and to response
    _ = await get_cache()
    cache = json.loads(_[0])
    assert isinstance(cache, list)
    compare(cache, [expected])
    compare(cache, original_response_json)
    # Step 3: Verify the cache corresponds to db
    from_db = await crud.get_all(get_test_session, model)
    compare(cache, from_db, exclude=EXCLUDE)
    # Step 4: Change db
    item_id, updated_data = __()
    await crud.update(get_test_session, model, item_id, **updated_data)
    # Step 5: Verify the cache does not correspond to db
    updated = await crud.get_all(get_test_session, model)
    with pytest.raises(AssertionError, match=REGEX):
        compare(cache, updated, exclude=EXCLUDE)
    # Step 6: Invoke service.get_all and verify result is from cache
    response_json = await request_get(async_client_unauthorized, view_name)
    assert response_json == original_response_json
    compare(response_json, cache)
    with pytest.raises(AssertionError, match=REGEX):
        compare(response_json, updated)


# ================ TEST NO CACHE ================
@pytest.mark.xfail(reason="No cache")
async def test__get_product_by_name_slug__fails_no_cache(
    async_client_unauthorized: AsyncClient,
    get_product: pm.ProductInDB,
    is_cache_empty,
) -> None:
    assert await is_cache_empty()
    _ = await request_get(
        async_client_unauthorized,
        view_name="product:get_product_by_name_slug",
        product_slug=get_product.name_slug,
    )
    assert not await is_cache_empty()


@parametrize_post
@pytest.mark.xfail(reason="No cache")
async def test__post__fails_no_cache(
    async_client_unauthorized: AsyncClient,
    view_name: str,
    get_product: pm.ProductInDB,
    is_cache_empty,
) -> None:
    assert await is_cache_empty()
    _ = await request_post(async_client_unauthorized, view_name, [get_product.id])
    assert not await is_cache_empty()


@pytest.mark.xfail(reason="No cache")
async def test__get_all_products__fails_no_cache(
    async_client_authorized: AsyncClient,
    get_product: pm.ProductInDB,
    is_cache_empty,
) -> None:
    assert await is_cache_empty()
    _ = await request_get(async_client_authorized, view_name="product:get_all")
    assert not await is_cache_empty()


@pytest.mark.xfail(reason="No cache")
async def test__get_product_name_by_id__fails_no_cache(
    async_client_authorized: AsyncClient,
    get_product: pm.ProductInDB,
    is_cache_empty,
) -> None:
    assert await is_cache_empty()
    _ = await request_get(
        async_client_authorized,
        view_name="product:get_name_by_id",
        product_id=get_product.id,
    )
    assert not await is_cache_empty()


@pytest.mark.xfail(reason="No cache")
async def test__get_document__fails_no_cache(
    async_client_authorized: AsyncClient,
    get_product: pm.ProductInDB,
    is_cache_empty,
) -> None:
    assert await is_cache_empty()
    _ = await request_get(
        async_client_authorized,
        view_name="product:get_document",
        document_id=get_product.documents[0].id,
        response_json=False,
    )
    assert not await is_cache_empty()


@pytest.mark.xfail(reason="No cache")
async def test__create_product__fails_no_cache(
    async_client_authorized, get_product_create_data, is_cache_empty
) -> None:
    assert await is_cache_empty()
    _ = await request_post(
        async_client_authorized,
        view_name="product:create",
        payload=get_product_create_data,
    )
    assert not await is_cache_empty()


@pytest.mark.xfail(reason="No cache")
async def test__update_product__fails_no_cache(
    async_client_authorized: AsyncClient,
    get_product,
    get_product_update_data,
    is_cache_empty,
) -> None:
    assert await is_cache_empty()
    _ = await request_patch(
        async_client_authorized,
        view_name="product:update",
        payload=get_product_update_data,
        product_id=get_product.id,
    )
    assert not await is_cache_empty()


@pytest.mark.parametrize(
    "current_status, new_status, is_active",
    ((ProductStatus.ready_for_sale, ProductStatusForChange.on_sale, True),),
)
@pytest.mark.xfail(reason="No cache")
async def test__change_product_status__fails_no_cache(
    monkeypatch,
    async_client_authorized,
    get_test_session,
    get_product,
    current_status,
    new_status,
    is_active,
    is_cache_empty,
) -> None:
    monkeypatch.setattr("app.services.seller_products.Service", mocks.MockServiceETL)
    await crud.update(
        get_test_session, pm.ProductInDB, get_product.id, status=current_status, is_active=bool(not is_active)
    )
    assert await is_cache_empty()
    await request_patch(
        async_client_authorized,
        view_name="product:change_status",
        product_id=get_product.id,
        query_params=f"?product_status={new_status.value}",
        response_json=False,
    )
    assert not await is_cache_empty()
