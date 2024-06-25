import pytest
from fastapi import status
from fastapi.exceptions import HTTPException

from app.main import app
from app.services.seller_products import Service
from tests import mocks as m
from tests.settings import settings as test_settings
from tests.utils import check_exception_info, reverse


async def test_get_response_from_external_service_raise_502_on_invalid_protocol(get_service: Service) -> None:
    with pytest.raises(HTTPException, match=r"Ошибка в получении данных от внешнего сервиса") as exc_info:
        await get_service._get_response_from_external_service("")
    check_exception_info(exc_info, expected_error_code=status.HTTP_502_BAD_GATEWAY)


async def test_get_response_from_external_service_raise_502_on_unsuccessfull_status_code(
    get_service: Service,
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.services.base.AsyncClient", m.MockAsyncClient)
    url = test_settings.test_service_dsn + reverse(app, "product:get_all")
    status_code = status.HTTP_403_FORBIDDEN
    expected_err_msg = f"Ошибка в получении данных от внешнего сервиса ({url}): status code {status_code}"
    with pytest.raises(HTTPException) as exc_info:
        await get_service._get_response_from_external_service(url, json={"status_code": status_code})
    check_exception_info(exc_info, expected_msg=expected_err_msg, expected_error_code=status.HTTP_502_BAD_GATEWAY)


async def test_get_response_from_external_service_returns_data(
    get_service: Service,
    monkeypatch,
) -> None:
    monkeypatch.setattr("app.services.base.AsyncClient", m.MockAsyncClient)
    url = test_settings.test_service_dsn + reverse(app, "product:get_all")
    status_code = status.HTTP_200_OK
    fake_data_from_external_service = {"product_id": str(m.UUID_ID), "storage_quantity": 10}
    data = await get_service._get_response_from_external_service(
        url, json={"status_code": status_code, "data": fake_data_from_external_service}
    )
    assert data == fake_data_from_external_service


@pytest.mark.parametrize(
    "method_name, err_msg",
    (
        ("_get_seller_data", r"Ошибка в получении данных о продавце товара:"),
        ("_get_product_storage_quantity", r"Ошибка в получении данных о количестве товара на складе:"),
    ),
)
async def test_service_method_raises_502(get_service_dependencies, method_name, err_msg) -> None:
    service = m.MockServiceExternalData(*get_service_dependencies)
    service.fake_external_data = "invalid_data"
    with pytest.raises(HTTPException, match=err_msg) as exc_info:
        await getattr(service, method_name)("")
    check_exception_info(exc_info, expected_error_code=status.HTTP_502_BAD_GATEWAY)


@pytest.mark.skip(reason="Do not know API spec for seller data from external service")
async def test_get_seller_data_returns_valid_data(get_service_dependencies) -> None:
    service = m.MockServiceExternalData(*get_service_dependencies)
    service.fake_external_data = {}  # where to see the API spec ???
    expected = None
    assert await service._get_seller_data(user_token="user_token") == expected


@pytest.mark.parametrize(
    "input_data, expected",
    (
        (None, 0),
        ([{"product_id": str(m.UUID_ID), "storage_quantity": 10}], 10),
    ),
)
async def test_get_seller_data_returns_valid_data(get_service_dependencies, input_data, expected) -> None:
    service = m.MockServiceExternalData(*get_service_dependencies)
    service.fake_external_data = input_data
    assert await service._get_product_storage_quantity(product_id=m.UUID_ID) == expected
