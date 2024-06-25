from typing import Callable

import pytest
from fastapi import Response, status
from httpx import AsyncClient


def check_definition(response: Response) -> None:
    assert response.json()["info"] == {
        "description": "Products API documentation",
        "title": "Products",
        "version": "v3",
    }


def check_docs(response: Response) -> None:
    # response contains HTML content (not a JSON)
    assert b"swagger-ui" in response._content


parametrize = pytest.mark.parametrize(
    "url, check_func",
    (
        ("/products/api/v3/definition", check_definition),
        ("/products/api/v2/docs", check_docs),
        ("/products/api/v3/docs", check_docs),
    ),
)


@parametrize
async def test_endpoints_docs(async_client_authorized: AsyncClient, url: str, check_func: Callable):
    response = await async_client_authorized.get(url)
    response.raise_for_status()
    check_func(response)


@parametrize
async def test_anon_has_no_access_docs(async_client_unauthorized: AsyncClient, url: str, check_func: Callable):
    response = await async_client_unauthorized.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
