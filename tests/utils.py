import base64
from http import HTTPStatus
from json import dumps
from pprint import pprint
from typing import Any, TypeAlias
from uuid import UUID

from faker import Faker
from fastapi import FastAPI, Response, status
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.fields_extensions_models import (
    ProductBrandInDB,
    ProductColorInDB,
    ProductDocumentInDB,
    ProductImageInDB,
    ProductSizeInDB,
)
from app.models.products_models import ProductCategoryInDB, ProductInDB, ProductSubCategoryInDB
from tests import crud

Json: TypeAlias = dict[str, Any]
Jsons: TypeAlias = list[Json]
ModelType: TypeAlias = Any


def info(*args, exc: bool = True) -> None:
    for arg in args:
        pprint(arg)
    if exc:
        assert 0


def check_exception_info(exc_info, expected_msg: str | None = None, expected_error_code: int | None = None) -> None:
    if expected_msg is not None:
        # assert exc_info.value.args[0] == expected_msg
        assert exc_info.value.detail == expected_msg
    if expected_error_code is not None:
        assert exc_info.value.status_code == expected_error_code


def get_image(image_format: str = "jpeg", size: int = 5) -> bytes:
    return Faker().image(image_format=image_format, size=(size, size))


def get_content(mime: str = "image", ext: str = "jpeg", data: str | None = None, data_size: int = 1) -> str:
    if data is None:
        data = base64.b64encode(get_image(size=data_size)).decode()
    assert isinstance(data, str)
    return "data:{mime}/{ext};base64,{data}".format(mime=mime, ext=ext, data=data)


def is_base64(item: str) -> None:
    assert isinstance(item, str)
    format_file, data = item.split(";base64,")
    assert format_file.startswith("data:")
    ext = format_file.split("/")[-1]
    assert ext in ("jpeg", "png", "pdf"), f"Not supported file format {ext}"
    remaining = len(data) % 4
    assert not remaining, f"Base64 data is not multiple of 4, remaining: {remaining}"


def is_valid_uuid(val) -> bool:
    try:
        UUID(str(val))
    except ValueError:
        assert 0, "Not valid UUID"
    return True


def to_json(entity: dict[str, Any] | BaseModel | list[BaseModel]) -> str:
    return dumps(jsonable_encoder(entity))


def reverse(app: FastAPI, view_name: str) -> str:
    for route in app.router.routes:
        if route.name == view_name:
            return route.path
    raise NotImplementedError(f"Path operation function `{view_name}` hasn't been implemented yet.")


def has_access(response: Response) -> bool:
    return response.status_code not in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN)


async def request_get(
    client: AsyncClient, view_name: str, status_code: int = status.HTTP_200_OK, response_json: bool = True, **path_param
) -> dict[str, Any] | Response:
    url = reverse(app, view_name).format(**path_param) if path_param else reverse(app, view_name)
    response = await client.get(url)
    assert response.status_code == status_code
    return response.json() if response_json else response


async def request_post(
    client: AsyncClient,
    view_name: str,
    payload: Any,
    exclude: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    url = reverse(app, view_name)
    response = await client.post(url, json=jsonable_encoder(payload, exclude=exclude))
    response.raise_for_status()
    return response.json()


async def request_patch(
    client: AsyncClient,
    view_name: str,
    payload: Any,
    exclude: tuple[str, ...] | None = None,
    status_code: int = 200,
    **path_param,
) -> dict[str, Any]:
    url = reverse(app, view_name).format(**path_param)
    response = await client.patch(url, json=jsonable_encoder(payload, exclude=exclude))
    assert response.status_code == status_code
    return response.json()


def compare(left: Any, right: Any, exclude: tuple[str, ...] | None = None) -> None:
    left_json, right_json = jsonable_encoder(left, exclude=exclude), jsonable_encoder(right, exclude=exclude)
    common_keys = set(left_json.keys()) & set(right_json.keys())
    assert common_keys, "Objects cannot be compared"
    for key in common_keys:
        assert left_json[key] == right_json[key], key


async def check_response_json(
    response_json: dict[str, Any],
    session: AsyncSession,
    model_class: ModelType,
    create_update_data: dict[str, Any] | None = None,
    exclude: tuple[str, ...] | None = None,
) -> None:
    assert is_valid_uuid(response_json["id"])
    from_db = await crud.get_or_404(session, model_class, response_json["id"])
    assert isinstance(from_db, model_class)
    compare(response_json, from_db, exclude=exclude)
    if create_update_data:
        compare(response_json, create_update_data, exclude=exclude)


async def check_obj(obj, model_class, session, create_data: dict[str, Any] | None = None) -> None:
    def _check_obj(obj) -> None:
        assert isinstance(obj, model_class)
        assert is_valid_uuid(obj.id)

    _check_obj(obj)
    from_db = await crud.get_or_404(session, model_class, obj.id)
    _check_obj(from_db)
    compare(obj, from_db)
    if create_data:
        compare(obj, create_data)


async def is_db_populated(session) -> bool:
    for model in (
        ProductCategoryInDB,
        ProductSubCategoryInDB,
        ProductBrandInDB,
        ProductSizeInDB,
        ProductColorInDB,
        ProductInDB,
        ProductImageInDB,
        ProductDocumentInDB,
    ):
        assert await crud.get_all(session, model), f"{model} is empty"
    return True
