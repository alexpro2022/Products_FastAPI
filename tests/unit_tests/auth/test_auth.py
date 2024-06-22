import pytest
from fastapi import status
from fastapi.exceptions import HTTPException

from app.core.config import settings
from app.middlewares.auth import api_key_auth


def test_api_key_auth_raises_exc():
    with pytest.raises(HTTPException) as exc_info:
        api_key_auth("invalid_api_key")
        assert status.HTTP_403_FORBIDDEN in exc_info.value.args


def test_api_key_auth_with_valid_input():
    api_key_auth(settings.app_settings.api_key)
