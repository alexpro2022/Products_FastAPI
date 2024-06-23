import base64
import io
from typing import Any
from uuid import uuid4

from botocore.response import StreamingBody
from fastapi import Request

from app.cache.cache import get_redis_client
from app.core.config import settings as app_settings
from app.db import get_session
from app.main import app
from app.middlewares.auth import SellerCheck
from app.mq import RabbitMQ
from tests.utils import get_image

UUID_ID = uuid4()
SELLER_ID = uuid4()
S3_IMAGE = get_image(size=1)


def mocker(*args, **kwargs):
    pass


async def amocker(*args, **kwargs):
    pass


def mocker_raise(*args, **kwargs):
    assert 0, "MOCKER"


async def amocker_raise(*args, **kwargs):
    assert 0, "AMOCKER"


class MockAuth:
    username: str = "test_username"
    password: str = "test_password"


class MockRabbitMQ(RabbitMQ):
    async def connect(*args, **kwargs):
        await amocker_raise()

    async def close_connections(*args, **kwargs):
        await amocker()


class MockValidationInfo:
    def __init__(self, **kwargs):
        self._kwargs = kwargs

    @property
    def data(self):
        return self._kwargs


class MockSellerCheck(SellerCheck):
    async def __call__(self, request: Request):
        setattr(request, "seller_id", str(SELLER_ID))


def override_sessions(db_session, cache_session) -> None:
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_redis_client] = lambda: cache_session


def mock_s3_client(*args, **kwargs) -> None:
    assert args[0] == "s3"
    assert kwargs["endpoint_url"] == app_settings.s3_settings.url
    assert kwargs["aws_access_key_id"] == app_settings.s3_settings.access_key
    assert kwargs["aws_secret_access_key"] == app_settings.s3_settings.secret_key

    class MockS3Client:
        @staticmethod
        def get_object(Bucket, Key) -> dict[str, Any]:
            assert isinstance(Bucket, str)
            assert isinstance(Key, str)
            assert Key.startswith("temp/products/documents/")
            data = base64.b64encode(S3_IMAGE)
            return {"Body": StreamingBody(io.BytesIO(data), len(data))}

        @staticmethod
        def upload_fileobj(fileobj, bucket, key, ExtraArgs) -> None:
            assert isinstance(fileobj, io.BytesIO)
            assert isinstance(bucket, str)
            assert isinstance(key, str)
            assert key.endswith(".jpeg")
            assert key.startswith("temp/products/images/") or key.startswith("temp/products/documents/")
            assert (
                (ExtraArgs == {"ACL": "public-read"})
                if key.startswith("temp/products/images/")
                else (ExtraArgs == {"ACL": "private"})
            )

    return MockS3Client
