from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlmodel import MetaData

from app import db
from app.core.config import settings
from tests import utils as u
from tests.fixtures.fixtures import metadata as expected_metadata
from tests.mocks import mocker_raise
from tests.unit_tests.db import data as d


@pytest.mark.parametrize(
    "entity, klass",
    (
        (db.engine, AsyncEngine),
        (db.metadata, MetaData),
        (db.async_session, async_sessionmaker),
        (db.get_session(), AsyncGenerator),
    ),
)
def test_entities(entity, klass):
    assert isinstance(entity, klass)


def test_metada_attributes():
    assert db.metadata.schema == expected_metadata.schema
    assert db.metadata.naming_convention == expected_metadata.naming_convention


async def test_get_session():
    async for session in db.get_session():
        assert isinstance(session, AsyncSession)


async def test_create_schema(monkeypatch, get_test_session):
    def mocker(*args, **kwargs):
        assert kwargs["text"] == f'CREATE SCHEMA IF NOT EXISTS "{settings.postgres_settings.schema_name}"'
        mocker_raise()

    monkeypatch.setattr("app.db.text", mocker)
    with pytest.raises(AssertionError, match="MOCKER"):
        await db.create_schema(get_test_session)


async def test_add_extensions(monkeypatch, get_test_session):
    def mocker(*args, **kwargs):
        assert kwargs["text"] == 'CREATE EXTENSION IF NOT EXISTS "one"'
        mocker_raise()

    monkeypatch.setattr("app.core.config.settings.postgres_settings.extensions", ["one"])
    monkeypatch.setattr("app.db.text", mocker)
    with pytest.raises(AssertionError, match="MOCKER"):
        await db.add_extensions(get_test_session)


async def test_init_config(get_test_session):
    assert await db.init_config(get_test_session) is None


async def test_close_connection(monkeypatch):
    class MockAsyncEngine(AsyncEngine):
        async def dispose(*args, **kwargs):
            mocker_raise()

    monkeypatch.setattr("app.db.engine", MockAsyncEngine)
    with pytest.raises(AssertionError, match="MOCKER"):
        await db.close_connection()


async def test_init_db(monkeypatch):
    from tests.fixtures.fixtures import engine

    monkeypatch.setattr("app.db.engine", engine)
    monkeypatch.setattr(
        "app.db.async_session",
        async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
        ),
    )
    await db.init_db()


@pytest.mark.parametrize(
    "entity, expected",
    (
        # (d.DICT, d.DICT_JSON),  TypeError: Object of type UUID is not JSON serializable
        (d.FLAT_BASE_MODEL, d.FLAT_BASE_MODEL_EXPECTED_JSON),
        (d.FLAT_BASE_MODELS, d.FLAT_BASE_MODELS_EXPECTED_JSON),
        # TypeError: Object of type date is not JSON serializable
        # (d.NESTED_BASE_MODEL, d.NESTED_BASE_MODEL_EXPECTED_JSON),
        # (d.NESTED_BASE_MODELS, d.NESTED_BASE_MODELS_EXPECTED_JSON),
    ),
)
def test_to_json(entity, expected):
    actual = db.to_json(entity)
    assert isinstance(actual, str)
    assert actual == expected


# Below is the new method "to_json" testing
@pytest.mark.parametrize(
    "entity, expected",
    (
        (d.DICT, d.DICT_JSON),
        (d.FLAT_BASE_MODEL, d.FLAT_BASE_MODEL_EXPECTED_JSON),
        (d.FLAT_BASE_MODELS, d.FLAT_BASE_MODELS_EXPECTED_JSON),
        (d.NESTED_BASE_MODEL, d.NESTED_BASE_MODEL_EXPECTED_JSON),
        (d.NESTED_BASE_MODELS, d.NESTED_BASE_MODELS_EXPECTED_JSON),
    ),
)
def test_new_to_json(entity, expected):
    actual = u.to_json(entity)
    assert isinstance(actual, str)
    assert actual == expected
