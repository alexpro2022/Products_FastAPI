import pytest
from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer

from app.api.setup import docs_basic_auth, get_oauth2_scheme
from app.core.config import settings
from tests.mocks import MockAuth
from tests.utils import check_exception_info


def test_get_oauth2_scheme() -> None:
    actual: OAuth2AuthorizationCodeBearer = get_oauth2_scheme("")
    assert actual.auto_error is False
    assert actual.model.flows.authorizationCode.authorizationUrl == "authorization"
    assert actual.model.flows.authorizationCode.tokenUrl == ""


def test_docs_basic_auth_returns_None(monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.settings.app_settings.docs_basic_credentials", None)
    assert docs_basic_auth() is None


@pytest.mark.parametrize(
    "auth, status_code",
    (
        (None, status.HTTP_401_UNAUTHORIZED),
        (MockAuth(), status.HTTP_403_FORBIDDEN),
    ),
)
def test_docs_basic_auth_raises(auth, status_code) -> None:
    with pytest.raises(HTTPException) as exc_info:
        docs_basic_auth(auth)
    check_exception_info(exc_info, expected_error_code=status_code)
