from http import HTTPStatus

import pytest
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import ORJSONResponse

from app.db import get_session
from app.main import get_application, health_check_handler, shutdown, startup, unicorn_exception_handler
from tests.mocks import MockRabbitMQ, amocker, amocker_raise


async def test_health_check_handler(get_test_session) -> None:
    assert await health_check_handler(get_test_session) == {"status": True}


async def test_health_check_handler_raises_exc() -> None:
    with pytest.raises(HTTPException, match="DB connection error"):
        async for session in get_session():
            setattr(session, "connection", amocker_raise)
            await health_check_handler(session)


@pytest.mark.parametrize(
    "exception, expected_attrs",
    (
        (HTTPException(401, "Unauthorized"), (401, "Unauthorized")),
        (HTTPException(403, "Forbidden"), (403, "Forbidden")),
        (HTTPException(404, "Not found"), (404, "Not found")),
        (TypeError, (500, HTTPStatus(500).phrase)),
        (ValueError, (500, HTTPStatus(500).phrase)),
        (AssertionError, (500, HTTPStatus(500).phrase)),
    ),
)
async def test_unicorn_exception_handler(exception, expected_attrs) -> None:
    status_code, detail = expected_attrs
    expected = ORJSONResponse(
        status_code=status_code,
        content={
            "status_code": status_code,
            "detail": detail,
        },
    )
    actual: ORJSONResponse = await unicorn_exception_handler(None, exception)
    assert actual.status_code == expected.status_code
    assert actual.body == expected.body


async def test_startup(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_rabbitmq", lambda: MockRabbitMQ)
    monkeypatch.setattr("app.main.init_db", amocker)
    with pytest.raises(AssertionError, match="AMOCKER"):
        await startup()


async def test_shutdown(monkeypatch) -> None:
    monkeypatch.setattr("app.main.get_rabbitmq", lambda: MockRabbitMQ)
    monkeypatch.setattr("app.main.close_connection", amocker_raise)
    with pytest.raises(AssertionError, match="AMOCKER"):
        await shutdown()


async def test_get_application() -> None:
    actual = get_application()
    assert isinstance(actual, FastAPI)
    actual.exception_handlers[Exception] == unicorn_exception_handler
    actual.router.default_response_class is ORJSONResponse
    actual.router.on_shutdown == shutdown
    actual.router.on_startup == startup
