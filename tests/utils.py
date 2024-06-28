import base64
import json
from http import HTTPStatus
from pprint import pprint
from typing import Any, Sequence, TypeAlias
from uuid import UUID

from faker import Faker
from fastapi import FastAPI, Response, status
from fastapi.encoders import jsonable_encoder
from httpx import AsyncClient
from pydantic import BaseModel
from pytest import ExceptionInfo, raises
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


def check_exception_info(
    exc_info: ExceptionInfo,
    expected_msg: str | None = None,
    expected_error_code: int | None = None,
) -> None:
    """Проверяет наличие сообщения и/или кода ошибки, если указаны.

    Args:
        exc_info (ExceptionInfo): Объект, возвращаемый методом pytest.raises.
        expected_msg (str | None, optional): Ожидаемое сообщение исключения. Defaults to None.
        expected_error_code (int | None, optional): Ожидаемый код ошибки исключения. Defaults to None.
    """
    if expected_msg is not None:
        assert exc_info.value.detail == expected_msg, exc_info.value.detail
    if expected_error_code is not None:
        assert exc_info.value.status_code == expected_error_code


def get_image(image_format: str = "jpeg", size: int = 5) -> bytes:
    """Создает изображение при помощи Faker.

    Args:
        image_format (str, optional): Формат изображения. Defaults to "jpeg".
        size (int, optional): Размер изображения. Defaults to 5.

    Returns:
        bytes: байтовое предсталение изображения выбранного формата.
    """
    return Faker().image(image_format=image_format, size=(size, size))


def get_content(
    mime: str = "image",
    ext: str = "jpeg",
    data: str | None = None,
    data_size: int = 1,
) -> str:
    """Формирует бинарные данные (изображение) в виде закодированной base64-строки для передачи по API в формате json.
       Создает изображение при помощи Faker, если данные не указаны в аргументе data.


    Args:
        mime (str, optional): Тип передаваемых данных. Defaults to "image".
        ext (str, optional): Формат передаваемых данных. Defaults to "jpeg".
        data (str | None, optional): Закодированые в формате base64 бинарные данные (изображение). Defaults to None.
        data_size (int, optional): Размер создаваемого по умолчанию изображения. Defaults to 1.

    Returns:
        str: base64-строка для передачи бинарных данных по API в формате json.
    """
    if data is None:
        data = base64.b64encode(get_image(size=data_size)).decode()
    assert isinstance(data, str)
    return "data:{mime}/{ext};base64,{data}".format(mime=mime, ext=ext, data=data)


def is_base64(item: str) -> None:
    """Проверяет строку на соответствие стандарту base64 для передачи бинарных данных по API в формате json.

    Args:
        item (str): строка
    """
    assert isinstance(item, str)
    format_file, data = item.split(";base64,")
    assert format_file.startswith("data:")
    ext = format_file.split("/")[-1]
    assert ext in ("jpeg", "png", "pdf"), f"Not supported file format {ext}"
    remaining = len(data) % 4
    assert not remaining, f"Base64 data is not multiple of 4, remaining: {remaining}"


def is_valid_uuid(val: Any) -> bool:
    """Проверяет является ли переданное значение валидным для создания UUID.

    Args:
        val (Any): любое значение

    Returns:
        bool: True если значение является валидным.
    """
    try:
        UUID(str(val))
    except ValueError:
        assert 0, "Not valid UUID"
    return True


def to_json(entity: dict[str, Any] | BaseModel | list[BaseModel]) -> str:
    """Сериализует объект в строку формата json.

    Args:
        entity (dict[str, Any] | BaseModel | list[BaseModel]): сериализуемый объект.

    Returns:
        str: строка формата json.
    """
    return json.dumps(jsonable_encoder(entity))


def reverse(app: FastAPI, view_name: str) -> str:
    """Аналог функции reverse в Джанго. По имени вью-функции возвращает url эндпойнта.

    Args:
        app (FastAPI): FastaAPI приложение
        view_name (str): имя вью-функции или значение аргумента `name` в декораторе вью-функции.

    Raises:
        NotImplementedError: исключение, если имя вью-функции не найдено в приложении.

    Returns:
        str: url эндпойнта.
    """
    for route in app.router.routes:
        if route.name == view_name:
            return route.path
    raise NotImplementedError(f"Path operation function `{view_name}` hasn't been implemented yet.")


def has_access(response: Response) -> bool:
    """Определяет доступность эндпойнта по статус коду ответа.

    Args:
        response (Response): ответ эндпойнта.

    Returns:
        bool: True если доступ к эндпойнту разрешен.
    """
    return response.status_code not in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN)


async def request_get(
    client: AsyncClient,
    view_name: str,
    status_code: int = status.HTTP_200_OK,
    response_json: bool = True,
    query_params: str = "",
    **path_param,
) -> dict[str, Any] | Response:
    """Вспомогательная функция для HTTP-запроса методом GET.

    Args:
        client (AsyncClient): асинхронный HTTP-клиент.
        view_name (str): имя вью-функции или значение аргумента `name` в декораторе вью-функции.
        status_code (int, optional): статус код ответа. Defaults to status.HTTP_200_OK.
        response_json (bool, optional): булево значение для возврата либо ответа целиком, либо тела ответа. Defaults to True.
        query_params (str, optional): параметры запроса. Defaults to "".
        **path_param: параметр пути запроса в виде ключ=значение.
    Returns:
        dict[str, Any] | Response: возвращает либо тело ответа либо ответ целиком.
    """
    url = reverse(app, view_name).format(**path_param) if path_param else reverse(app, view_name)
    url += query_params
    response = await client.get(url)
    assert response.status_code == status_code
    return response.json() if response_json else response


async def request_post(
    client: AsyncClient,
    view_name: str,
    payload: Any,
    exclude: tuple[str, ...] | None = None,
    response_json: bool = True,
    query_params: str = "",
) -> dict[str, Any] | Response:
    """Вспомогательная функция для HTTP-запроса методом POST.

    Args:
        client (AsyncClient): асинхронный HTTP-клиент.
        view_name (str): имя вью-функции или значение аргумента `name` в декораторе вью-функции.
        payload (Any): JSON сериализуемый объект для включения в тело запроса.
        exclude (tuple[str, ...] | None, optional): кортеж имен полей, исключаемых из итогового JSON объекта. Defaults to None.
        response_json (bool, optional): булево значение для возврата либо ответа целиком, либо тела ответа. Defaults to True.
        query_params (str, optional): параметры запроса. Defaults to "".
    Returns:
        dict[str, Any] | Response: возвращает либо тело ответа либо ответ целиком.
    """
    url = reverse(app, view_name) + query_params
    response = await client.post(url, json=jsonable_encoder(payload, exclude=exclude))
    response.raise_for_status()
    return response.json() if response_json else response


async def request_patch(
    client: AsyncClient,
    view_name: str,
    payload: Any | None = None,
    exclude: tuple[str, ...] | None = None,
    status_code: int = 200,
    response_json: bool = True,
    query_params: str = "",
    **path_param,
) -> dict[str, Any] | Response:
    """Вспомогательная функция для HTTP-запроса методом PATCH.

    Args:
        client (AsyncClient): асинхронный HTTP-клиент.
        view_name (str): имя вью-функции или значение аргумента `name` в декораторе вью-функции.
        payload (Any): JSON сериализуемый объект для включения в тело запроса.
        exclude (tuple[str, ...] | None, optional): кортеж имен полей, исключаемых из итогового JSON объекта. Defaults to None.
        status_code (int, optional): статус код ответа. Defaults to status.HTTP_200_OK.
        response_json (bool, optional): булево значение для возврата либо ответа целиком, либо тела ответа. Defaults to True.
        query_params (str, optional): параметры запроса. Defaults to "".
        **path_param: параметр пути запроса в виде ключ=значение.
    Returns:
        dict[str, Any] | Response: возвращает либо тело ответа либо ответ целиком.
    """
    url = reverse(app, view_name).format(**path_param) + query_params
    response = await client.patch(url, json=jsonable_encoder(payload, exclude=exclude))
    assert response.status_code == status_code
    return response.json() if response_json else response


def compare(left: Any | list[Any], right: Any | list[Any], exclude: tuple[str, ...] | None = None) -> None:
    """Сравнивает два объекта через их JSON сериализуемые представления.

    Args:
        left (Any): объект сравнения.
        right (Any): объект сравнения.
        exclude (tuple[str, ...] | None, optional): кортеж имен полей, исключаемых из сравнения. Defaults to None.
    """

    def _compare(left: Any, right: Any) -> None:
        left_json, right_json = jsonable_encoder(left, exclude=exclude), jsonable_encoder(right, exclude=exclude)
        common_keys = set(left_json.keys()) & set(right_json.keys())
        assert common_keys, "Objects cannot be compared"
        for key in common_keys:
            assert left_json[key] == right_json[key], (key, left_json[key], right_json[key])

    if isinstance(left, Sequence) and isinstance(right, Sequence):
        for ll, rr in zip(left, right):
            _compare(ll, rr)
    else:
        _compare(left, right)


async def check_response_json(
    response_json: dict[str, Any],
    session: AsyncSession,
    model_class: ModelType,
    create_update_data: dict[str, Any] | None = None,
    exclude: tuple[str, ...] | None = None,
) -> None:
    """Проверяет ответ HTTP-запроса, сравнивая объект ответа с соотвествующим объектом в БД,
    а также с опциональными данными создания/редактирования объекта.

    Args:
        response_json (dict[str, Any]): тело ответа.
        session (AsyncSession): сессия подключения к БД.
        model_class (ModelType): название модели объекта в БД.
        create_update_data (dict[str, Any] | None, optional): данные создания/редактирования объекта. Defaults to None.
        exclude (tuple[str, ...] | None, optional): кортеж имен полей, исключаемых из сравнения. Defaults to None.
    """
    assert is_valid_uuid(response_json["id"])
    from_db = await crud.get_or_404(session, model_class, response_json["id"])
    assert isinstance(from_db, model_class)
    compare(response_json, from_db, exclude=exclude)
    if create_update_data:
        compare(response_json, create_update_data, exclude=exclude)


async def check_obj(
    obj: Any,
    session: AsyncSession,
    model_class: ModelType,
    create_update_data: dict[str, Any] | None = None,
) -> None:
    """Проверяет объект, сравнивая его с соотвествующим объектом в БД,
    а также с опциональными данными создания/редактирования объекта.

    Args:
        obj (_type_): проверяемый объект
        session (AsyncSession): сессия подключения к БД.
        model_class (ModelType): название модели объекта в БД.
        create_update_data (dict[str, Any] | None, optional): данные создания/редактирования объекта. Defaults to None.
    """

    def _check_obj(obj) -> None:
        assert isinstance(obj, model_class)
        assert is_valid_uuid(obj.id)

    _check_obj(obj)
    from_db = await crud.get_or_404(session, model_class, obj.id)
    _check_obj(from_db)
    compare(obj, from_db)
    if create_update_data:
        compare(obj, create_update_data)


async def is_db_populated(session: AsyncSession) -> bool:
    """Вспомогательная функция проверки заполненности БД.

    Args:
        session (AsyncSession): сессия подключения к БД.

    Returns:
        bool: True если БД заполнена.
    """
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
