from functools import lru_cache
from typing import Any, AsyncGenerator

from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis

from app.core.config import settings


class Cache:
    """Класс, представляющией кэширование через Redis."""

    def __init__(self, redis: Redis) -> None:
        self.redis: Redis = redis

    async def ping(
        self,
    ) -> Any:
        """Пингует Redis."""
        return self.redis.ping()

    async def get_value(
        self,
        key: str,
    ) -> str | None:
        """Получить значение из кэша."""
        result: str = await self.redis.get(name=key)
        return result

    async def set_value(
        self,
        key: str,
        value: str,
        expire: int = 60,
    ) -> None:
        """Установить значение в кэш."""
        await self.redis.set(
            name=key,
            value=value,
            ex=expire,
        )

    async def set_value_no_depends(
        self,
        key: str,
        value: str,
        expire: int,
    ) -> None:
        """Установить значение в кэш."""
        self.redis.set(
            name=key,
            value=value,
            ex=expire,
        )

    async def del_value(
        self,
        key: str,
    ) -> None:
        """Удалить значение из кэша."""
        await self.redis.delete(key)


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """Отдаёт клиент Redis-a."""
    redis: Redis = Redis.from_url(
        url=settings.redis_settings.dsn,
        encoding="utf-8",
        decode_responses=True,
    )

    if not redis:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    async with redis.client() as client:
        yield client


@lru_cache()
def get_cache(
    redis: Redis = Depends(
        dependency=get_redis_client,
    ),
) -> Cache:
    return Cache(
        redis=redis,
    )
