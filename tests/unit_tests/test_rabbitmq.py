import pytest

from app.core.config import settings
from app.mq import MQ, RabbitMQ, get_rabbitmq, mq


def test_mq():
    assert isinstance(mq, MQ)
    assert mq.rabbitmq.host == settings.mq_settings.host
    assert mq.rabbitmq.username == settings.mq_settings.username
    assert mq.rabbitmq.password == settings.mq_settings.password


def test_get_rabbitmq():
    assert isinstance(get_rabbitmq(), RabbitMQ)


@pytest.mark.skip(reason="Needs a rabbitmq service in docker-compose")
async def test_get_connection():
    await mq.rabbitmq.get_connection()
