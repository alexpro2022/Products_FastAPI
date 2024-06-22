import base64

import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app
from app.models.products_models import ProductInDB
from tests.mocks import S3_IMAGE, UUID_ID
from tests.utils import check_response_json, compare, request_get, request_patch, request_post, reverse


@pytest.mark.parametrize(
    "view_name, method",
    (
        ("product:get_all", "get"),
        ("product:get_name_by_id", "get"),
        ("product:get_document", "get"),
        ("product:create", "post"),
        ("product:update", "patch"),
    ),
)
async def test_anon_has_no_access(async_client_unauthorized: AsyncClient, view_name: str, method: str) -> None:
    url = reverse(app, view_name)
    response = await getattr(async_client_unauthorized, method)(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.parametrize(
    "view_name, method, path_param_name",
    (
        ("product:get_name_by_id", "get", "product_id"),
        ("product:get_document", "get", "document_id"),
        ("product:update", "patch", "product_id"),
    ),
)
async def test_get_returns_not_found(
    async_client_authorized: AsyncClient, view_name: str, method: str, path_param_name: str
) -> None:
    url = reverse(app, view_name).format(**{path_param_name: UUID_ID})
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


async def test_post_without_media(async_client_authorized, get_product_create_data, get_test_session) -> None:
    exclude = ("images", "documents")
    response_json = await request_post(
        async_client_authorized,
        view_name="product:create",
        payload=get_product_create_data,
        exclude=exclude,
    )
    await check_response_json(response_json, get_test_session, ProductInDB, get_product_create_data, exclude=exclude)


async def test_post_with_media(async_client_authorized, get_product_create_data, get_test_session) -> None:
    response_json = await request_post(
        async_client_authorized,
        view_name="product:create",
        payload=get_product_create_data,
    )
    await check_response_json(response_json, get_test_session, ProductInDB)


async def test_patch_product(
    async_client_authorized: AsyncClient, get_product, get_product_update_data, get_test_session
) -> None:
    response_json = await request_patch(
        async_client_authorized,
        view_name="product:update",
        payload=get_product_update_data,
        product_id=get_product.id,
    )
    await check_response_json(response_json, get_test_session, ProductInDB, get_product_update_data)
