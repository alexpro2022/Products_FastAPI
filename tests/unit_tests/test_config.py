import pytest

from app.core.config import AppSettings, PostgresSettings
from tests.mocks import MockValidationInfo


@pytest.mark.parametrize(
    "value, expected, environment",
    (
        (True, True, None),
        (False, False, None),
        (None, True, "development"),
        (None, False, "production"),
    ),
)
def test_build_is_debug(value, expected, environment) -> None:
    actual = AppSettings.build_is_debug(value, info=MockValidationInfo(environment=environment))
    assert actual == expected


@pytest.mark.parametrize(
    "value, expected, is_debug",
    (
        ("test", "test", None),
        (None, "DEBUG", True),
        (None, "INFO", False),
    ),
)
def test_build_log_level(value, expected, is_debug) -> None:
    actual = AppSettings.build_log_level(value, info=MockValidationInfo(is_debug=is_debug))
    assert actual == expected


@pytest.mark.parametrize(
    "value, expected, docs_username, docs_password",
    (
        ("test", "test", None, None),
        (None, "docs_username:docs_password", "docs_username", "docs_password"),
        (None, "docs_username", "docs_username", None),
        (None, "docs_password", None, "docs_password"),
    ),
)
def test_build_basic_credentials(value, expected, docs_username, docs_password) -> None:
    actual = AppSettings.build_basic_credentials(
        value, info=MockValidationInfo(docs_username=docs_username, docs_password=docs_password)
    )
    assert actual == expected


@pytest.mark.parametrize(
    "value, expected",
    (
        ("test", "test"),
        (None, "http://username:password@host:5432/db_name"),
        ("", "http://username:password@host:5432/db_name"),
    ),
)
def test_build_dsn(value, expected) -> None:
    actual = PostgresSettings.build_dsn(
        value,
        info=MockValidationInfo(
            protocol="http",
            username="username",
            password="password",
            host="host",
            port=5432,
            db_name="db_name",
        ),
    )
    assert actual == expected
