import asyncio
import json
from abc import ABC
from datetime import datetime
from logging import ERROR
from typing import Any, Coroutine, Mapping
from uuid import UUID

import boto3
from backoff import expo, on_exception
from fastapi import HTTPException, status
from httpx import AsyncClient
from httpx import Request as httpx_Request
from httpx import Response as httpx_Response
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import TextClause
from sqlmodel.sql.expression import SelectOfScalar

from app.cache import Cache
from app.core.config import settings
from app.mq.rabbitmq import RabbitMQ
from app.schemas.fields_extensions_schemas import FileObject


class Base(ABC):
    def __init__(
        self,
        session: AsyncSession,
        cache: Cache,
        rabbit_mq: RabbitMQ,
    ) -> None:
        self.session: AsyncSession = session
        self.cache: Cache = cache
        self.rabbit_mq: RabbitMQ = rabbit_mq

    @property
    def client(self) -> AsyncClient:
        return AsyncClient()

    async def _get_response_from_external_service(
        self,
        service_url: str,
        method="GET",
        json: dict[Any, Any] | list[Any] = None,
        headers: str = None,
    ) -> dict[str, Any]:
        """Совершает запрос к внешнему сервису,
        получает от него данные в виде json и
        преобразует их в соответветствующий тип данных Python

        Args:
            service_url (str): URL внешнего сервиса
            method (str, optional): метод http-запроса. Defaults to "GET".
            json (dict[Any, Any] | list[Any], optional): body-параметры в виде json. Defaults to None.
            headers (str, optional): http-headers, например, параметры для авторизации. Defaults to None.

        Raises:
            HTTPException: в случае ошибки получения данных от внешнего сервиса

        Returns:
            Any: ответ от внешнего сервиса в виде json, преобразованный в соответвтвующий тип данных Python
        """
        async with self.client as client:
            try:
                response: httpx_Response = await client.send(
                    request=httpx_Request(
                        url=service_url,
                        method=method,
                        headers=headers,
                        json=json,
                    )
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Ошибка в получении данных от внешнего сервиса ({service_url}): {str(exc)}",
                )

            if not response.is_success:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=(
                        f"Ошибка в получении данных от внешнего сервиса ({service_url}): status code"
                        f" {response.status_code}"
                    ),
                )

            return response.json()

    @on_exception(wait_gen=expo, exception=Exception, max_tries=5, backoff_log_level=ERROR)
    async def _get_count(
        self,
        statement: TextClause,
    ) -> int:
        count_result: Result = await self.session.execute(
            statement=statement,
        )

        if count := count_result.scalar_one_or_none():
            return int(count)
        else:
            return 0

    @on_exception(
        wait_gen=expo,
        exception=(Exception,),
        max_tries=5,
        backoff_log_level=ERROR,
    )
    async def _get_all(
        self,
        count: int,
        statement: SelectOfScalar[Any],
    ) -> list[Any]:
        if count:
            result: Result = await self.session.execute(
                statement=statement,
            )

            return result.scalars().all()
        else:
            return []

    @on_exception(
        wait_gen=expo,
        exception=(Exception,),
        max_tries=5,
        backoff_log_level=ERROR,
    )
    async def _get_all_no_count(
        self,
        statement: SelectOfScalar[Any],
    ) -> list[Any]:
        result: Result = await self.session.execute(
            statement=statement,
        )

        return result.scalars().all()

    async def _get_one(
        self,
        statement: SelectOfScalar[Any],
    ) -> Any:
        result: Result = await self.session.execute(
            statement=statement,
        )
        if instance_in_db := result.scalars().one_or_none():
            return instance_in_db
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
        )

    @on_exception(
        wait_gen=expo,
        exception=(Exception,),
        max_tries=5,
        backoff_log_level=ERROR,
    )
    async def _create(
        self,
        instances: list[Any],
    ) -> list[Any]:
        self.session.add_all(
            instances=instances,
        )

        await self.session.commit()

        for instance in instances:
            await self.session.refresh(
                instance=instance,
            )

        return instances

    @on_exception(
        wait_gen=expo,
        exception=(Exception,),
        max_tries=5,
        backoff_log_level=ERROR,
    )
    async def _create_one(self, instance: Any) -> Any:
        self.session.add(instance=instance)
        await self.session.commit()
        await self.session.refresh(instance=instance)
        return instance

    @on_exception(
        wait_gen=expo,
        exception=(Exception,),
        max_tries=5,
        backoff_log_level=ERROR,
    )
    async def _update(
        self,
        instance: Mapping[str, Any],
        statement: SelectOfScalar[Any],
    ) -> Any:
        result: Result = await self.session.execute(
            statement=statement,
        )
        items = instance.items() if isinstance(instance, dict) else instance.dict().items()
        if instance_in_db := result.scalars().one_or_none():
            for key, value in items:
                setattr(instance_in_db, key, value)

            self.session.add(
                instance=instance_in_db,
            )

            await self.session.commit()
            await self.session.refresh(
                instance=instance_in_db,
            )

            return instance_in_db
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
            )

    async def _update_instance(
        self,
        instances: list[Any],
    ) -> list[Any]:
        self.session.add_all(
            instances=instances,
        )

        await self.session.commit()

        for instance in instances:
            for key, value in vars(instance).items():
                setattr(instance, key, value)
        await self.session.refresh(
            instance=instance,
        )

    async def _delete(
        self,
        statement: SelectOfScalar[Any],
    ) -> None:
        result: Result = await self.session.execute(
            statement=statement,
        )

        if instance_in_db := result.scalar_one_or_none():
            await self.session.delete(
                instance=instance_in_db,
            )

            await self.session.commit()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instance not exists",
            )

    @on_exception(
        wait_gen=expo,
        exception=(Exception,),
        max_tries=5,
        backoff_log_level=ERROR,
    )
    async def _delete_all(
        self,
        statement: Select,
        is_response: bool = True,
    ) -> None:
        result: Result = await self.session.execute(
            statement=statement,
        )

        if instances_in_db := result.scalars().all():

            for instance_in_db in instances_in_db:
                await self.session.delete(
                    instance=instance_in_db,
                )

            await self.session.commit()
        elif is_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Instance not exists",
            )

    def _list_data_db_conversion(
        self,
        db_data: list[Any],
        relationships: list[str],
    ) -> list[dict[str, Any]]:
        """Преобразование данных из БД в базовые типы."""
        cache_data = []
        for data in db_data:
            relationships_data = {}
            for key in relationships:
                relationship_data = getattr(data, key)
                relationships_data[key] = self._list_data_db_conversion(relationship_data, [])
            data: dict[str, Any] = data.model_dump()
            for key, value in data.items():
                if isinstance(value, (UUID, datetime)):
                    data[key] = str(value)
            cache_data.append(data | relationships_data)
        return cache_data

    async def _get_data_in_cache_or_db(
        self,
        coroutine: Coroutine,
        cache_key: str,
        relationships: list[str] | None = None,
    ) -> dict[str, Any]:
        """Отдаёт данные из кэша или базы данных."""
        if relationships is None:
            relationships = []
        if cache_data := await self.cache.get_value(cache_key):
            return json.loads(cache_data)
        db_data = await coroutine
        cache_data = self._list_data_db_conversion(db_data, relationships)
        await self.cache.set_value(cache_key, json.dumps(cache_data, ensure_ascii=False).encode("utf8"))
        return cache_data

    @property
    def s3_client(self):
        """Геттер клиента s3."""
        return boto3.client(
            "s3",
            endpoint_url=settings.s3_settings.url,
            aws_access_key_id=settings.s3_settings.access_key,
            aws_secret_access_key=settings.s3_settings.secret_key,
        )

    async def _delete_file_to_s3(self, file_url: str, bucket: str) -> None:
        """Удаление файла из объектного хранилища."""
        try:
            key = file_url.split(f"{bucket}/")[1]
            await asyncio.to_thread(
                self.s3_client.delete_object,
                Bucket=bucket,
                Key=key,
            )
        except Exception as err:
            raise HTTPException(500, detail=f"Ошибка при удалении файла: {str(err)}")

    async def _multi_delete_files_to_s3(self, file_urls: list[str], bucket: str) -> None:
        """Удаление файлов из объектного хранилища."""
        keys = [{"Key": file_url.split(f"{bucket}/")[-1]} for file_url in file_urls]
        try:
            if keys:
                await asyncio.to_thread(
                    self.s3_client.delete_objects,
                    Bucket=bucket,
                    Delete={"Objects": keys},
                )
        except Exception as err:
            raise HTTPException(500, detail=f"Ошибка при удалении файлов: {str(err)}")

    async def _upload_file_to_s3(
        self,
        file_object: FileObject,
        bucket: str,
        public: bool,
    ) -> FileObject:
        """Создание файла в объектном хранилище."""
        extra_args = {"ACL": "public-read"} if public else {"ACL": "private"}
        try:
            await asyncio.to_thread(
                self.s3_client.upload_fileobj,
                file_object.file_object,
                bucket,
                f"temp/{file_object.storage_path}",
                ExtraArgs=extra_args,
            )
        except Exception as err:
            raise HTTPException(500, detail=f"Ошибка при загрузке файла: {str(err)}")
        return file_object

    async def _multi_upload_files_to_s3(
        self,
        file_objects: list[FileObject],
        bucket: str,
        public: bool = True,
    ) -> list[FileObject]:
        """Создание файлов в объектном хранилище."""
        tasks = [
            asyncio.create_task(
                self._upload_file_to_s3(
                    file_object=file_object,
                    bucket=bucket,
                    public=public,
                )
            )
            for file_object in file_objects
        ]
        return await asyncio.gather(*tasks)

    async def _get_file_in_s3(self, key: str, bucket: str) -> dict[str, Any]:
        """Получение файла из хранилища."""
        return await asyncio.to_thread(
            self.s3_client.get_object,
            Bucket=bucket,
            Key=key,
        )
