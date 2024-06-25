import base64

import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app
from app.models.fields_extensions_models import ProductStatus, ProductStatusForChange
from app.models.products_models import ProductInDB
from tests import crud, mocks
from tests.mocks import S3_IMAGE, UUID_ID
from tests.utils import check_response_json, compare, info, request_get, request_patch, request_post, reverse


@pytest.mark.parametrize(
    "view_name, method",
    (
        ("product:get_all", "get"),
        ("product:get_name_by_id", "get"),
        ("product:get_document", "get"),
        ("product:create", "post"),
        ("product:update", "patch"),
        ("product:change_status", "patch"),
    ),
)
async def test_anon_has_no_access(async_client_unauthorized: AsyncClient, view_name: str, method: str) -> None:
    url = reverse(app, view_name)
    response = await getattr(async_client_unauthorized, method)(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize(
    "view_name, method, path_param_name, query_param",
    (
        ("product:get_name_by_id", "get", "product_id", ""),
        ("product:get_document", "get", "document_id", ""),
        ("product:update", "patch", "product_id", ""),
        ("product:change_status", "patch", "product_id", "?product_status=Продаётся"),
    ),
)
async def test_get_returns_not_found(
    async_client_authorized: AsyncClient, view_name: str, method: str, path_param_name: str, query_param: str
) -> None:
    url = reverse(app, view_name).format(**{path_param_name: UUID_ID}) + query_param
    kwargs = {"url": url, "json": {"name": "name"}} if method == "patch" else {"url": url}
    response = await getattr(async_client_authorized, method)(**kwargs)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Not Found"}


async def test_get_all_products_returns_empty_list(async_client_authorized: AsyncClient) -> None:
    response_json = await request_get(async_client_authorized, view_name="product:get_all")
    expected = {"page": 1, "size": 10, "totalCount": 0, "totalPages": 1, "results": []}
    assert response_json == expected


async def test_get_all_products_returns_objs_list(
    async_client_authorized: AsyncClient,
    get_product: ProductInDB,
) -> None:
    response_json = await request_get(async_client_authorized, view_name="product:get_all")
    results = response_json.pop("results")
    assert response_json == {"page": 1, "size": 10, "totalCount": 1, "totalPages": 1}
    for result in results:
        compare(result, get_product)


async def test_get_product_name_by_id_returns_obj(
    async_client_authorized: AsyncClient, get_product: ProductInDB
) -> None:
    response_json = await request_get(
        async_client_authorized,
        view_name="product:get_name_by_id",
        product_id=get_product.id,
    )
    compare(response_json, get_product)


async def test_get_document_returns_obj(async_client_authorized: AsyncClient, get_product: ProductInDB) -> None:
    document = get_product.documents[0]
    response = await request_get(
        async_client_authorized,
        view_name="product:get_document",
        document_id=document.id,
        response_json=False,
    )
    assert base64.b64decode(response._content) == S3_IMAGE


async def test_create_product_without_media(async_client_authorized, get_product_create_data, get_test_session) -> None:
    exclude = ("images", "documents")
    response_json = await request_post(
        async_client_authorized,
        view_name="product:create",
        payload=get_product_create_data,
        exclude=exclude,
    )
    await check_response_json(response_json, get_test_session, ProductInDB, get_product_create_data, exclude=exclude)


async def test_create_product_with_media(async_client_authorized, get_product_create_data, get_test_session) -> None:
    response_json = await request_post(
        async_client_authorized,
        view_name="product:create",
        payload=get_product_create_data,
    )
    await check_response_json(response_json, get_test_session, ProductInDB)


async def test_update_product(
    async_client_authorized: AsyncClient, get_product, get_product_update_data, get_test_session
) -> None:
    response_json = await request_patch(
        async_client_authorized,
        view_name="product:update",
        payload=get_product_update_data,
        product_id=get_product.id,
    )
    await check_response_json(response_json, get_test_session, ProductInDB, get_product_update_data)


async def test_change_product_status_returns_422(monkeypatch, async_client_authorized):
    monkeypatch.setattr("app.services.seller_products.Service", mocks.MockServiceETL)
    response_json = await request_patch(
        async_client_authorized,
        view_name="product:change_status",
        product_id=UUID_ID,
        query_params="?product_status=Новый",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    )
    assert (
        response_json["detail"][0]["msg"] == "Input should be 'Продаётся', 'Снят с продажи', 'На модерации' or 'Удалён'"
    )


async def test_change_product_status_returns_406(async_client_authorized: AsyncClient, get_product) -> None:
    response_json = await request_patch(
        async_client_authorized,
        view_name="product:change_status",
        product_id=get_product.id,
        query_params="?product_status=Продаётся",
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
    )
    assert response_json["detail"] == "Невозможно установить данный статус при текущем статусе продукта (Новый)"


@pytest.mark.parametrize(
    "current_status, new_status, is_active",
    (
        (ProductStatus.ready_for_sale, ProductStatusForChange.on_sale, True),
        (ProductStatus.on_sale, ProductStatusForChange.not_for_sale, False),
        (ProductStatus.new, ProductStatusForChange.on_moderation, False),
        (ProductStatus.needs_fix, ProductStatusForChange.on_moderation, False),
        (ProductStatus.on_sale, ProductStatusForChange.deleted, False),
        (ProductStatus.new, ProductStatusForChange.deleted, False),
        (ProductStatus.on_moderation, ProductStatusForChange.deleted, False),
        (ProductStatus.ready_for_sale, ProductStatusForChange.deleted, False),
        (ProductStatus.needs_fix, ProductStatusForChange.deleted, False),
        (ProductStatus.not_for_sale, ProductStatusForChange.deleted, False),
    ),
)
async def test_change_product_status_changes_product_in_db(
    monkeypatch, async_client_authorized, get_test_session, get_product, current_status, new_status, is_active
) -> None:
    monkeypatch.setattr("app.services.seller_products.Service", mocks.MockServiceETL)
    await crud.update(
        get_test_session, ProductInDB, get_product.id, status=current_status, is_active=bool(not is_active)
    )
    await request_patch(
        async_client_authorized,
        view_name="product:change_status",
        product_id=get_product.id,
        query_params=f"?product_status={new_status.value}",
        response_json=False,
    )
    product_in_db: ProductInDB = await crud.get_or_404(get_test_session, ProductInDB, get_product.id)
    assert product_in_db.status == new_status
    assert product_in_db.is_active == is_active
