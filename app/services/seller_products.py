from functools import lru_cache
from io import BytesIO
from math import ceil
from posixpath import join
from typing import Any
from uuid import UUID, uuid4

import orjson
from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, HTTPException, Response, status
from fastapi.encoders import jsonable_encoder
from PIL import Image
from PIL.Image import Image as OpenImage
from slugify.slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import SQLModel, select

from app.cache import Cache, get_cache
from app.core.config import image_sizes, settings
from app.db import get_session
from app.models.fields_extensions_models import (
    ProductBrandInDB,
    ProductColorInDB,
    ProductDocumentInDB,
    ProductImageInDB,
    ProductManuallyFilledSpecificationInDB,
    ProductPackInDB,
    ProductPriceInDB,
    ProductSizeInDB,
    ProductStatus,
    ProductStatusForChange,
)
from app.models.products_models import ProductCategoryInDB, ProductInDB, ProductSubCategoryInDB
from app.models.requests import RequestInfo
from app.mq import get_rabbitmq
from app.mq.rabbitmq import RabbitMQ
from app.schemas.fields_extensions_schemas import FileObject, ProductStorageQuantity, SellerData
from app.schemas.products_schemas import (
    ProductCreate,
    ProductForElastic,
    ProductPagination,
    ProductRead,
    ProductUpdate,
    ReadProductName,
)
from app.services.base import Base

load_dotenv()


LinkFields = tuple[tuple[str, SQLModel, UUID | None]]


class Service(Base):
    def __init__(self, session: AsyncSession, cache: Cache, rabbit_mq: RabbitMQ) -> None:
        super().__init__(session=session, cache=cache, rabbit_mq=rabbit_mq)

    does_not_exist_message = 'object "{}" does not exist'

    async def _check_for_records_in_tables(self, link_fields: LinkFields) -> dict[str, str]:
        """Валидация наличия записей в таблицах."""
        errors = {}
        for name, model, data in link_fields:
            if data is None:
                continue
            exists: int = await self._get_count(
                statement=select(func.count())
                .select_from(
                    model,
                )
                .where(
                    model.id == data,
                ),
            )
            if not exists:
                errors[name] = self.does_not_exist_message.format(data)
        return errors

    async def _validation_link_fields(self, link_fields: LinkFields) -> None:
        """Валидация на существование записей."""
        errors = await self._check_for_records_in_tables(link_fields)
        if errors:
            raise HTTPException(status_code=422, detail=errors)

    async def _list_validation_link_fields(self, list_link_fields: list[LinkFields]) -> None:
        """Валидация списка данных на существование записей."""
        list_errors = []
        for link_fields in list_link_fields:
            errors = await self._check_for_records_in_tables(link_fields)
            if errors:
                list_errors.append(errors)
        if list_errors:
            raise HTTPException(status_code=422, detail=list_errors)

    def _check_access_to_product(self, product_in_db: ProductInDB, seller_id: str) -> None:
        """Проверяет доступ продавца к товару."""
        if str(product_in_db.seller_id) == seller_id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )

    def _validation_order_num(self, order_num: list[int]) -> None:
        """Валидирует порядок изображений."""
        order_num = sorted(order_num)
        for index, num in enumerate(order_num):
            if index != num:
                raise HTTPException(status_code=422, detail={"order_num": "incorrect image order"})

    def _get_delete_update_create_images(
        self,
        product_images: list[ProductImageInDB],
        images: list[dict],
    ) -> tuple[list[UUID], list[dict], list[dict]]:
        """Отдаёт изображения для удаления, изменения и создания."""
        product_images_id = {product_image.id: product_image.id for product_image in product_images}
        update_product_images = []
        create_product_images = []
        order_num = []
        list_errors = []
        for image in images:
            order_num.append(image["order_num"])
            image_id = image.get("id")
            if not image_id:
                create_product_images.append(image)
                continue
            if image_id not in product_images_id:
                list_errors.append({"id": self.does_not_exist_message.format(image_id)})
                continue
            update_product_images.append(image)
            product_images_id.pop(image_id)
        if list_errors:
            raise HTTPException(status_code=422, detail=list_errors)
        delete_product_images = product_images_id.keys()
        self._validation_order_num(order_num)
        return delete_product_images, update_product_images, create_product_images

    async def _delete_product_images(self, delete_product_images: list[UUID]) -> None:
        """Удаляет изображения продукта."""
        product_images_in_db: list[ProductImageInDB] = await self._get_all(
            statement=select(ProductImageInDB).where(
                ProductImageInDB.id.in_(delete_product_images),
            ),
            count=1,
        )
        images_delete = []
        for product_image_in_db in product_images_in_db:
            images_delete.extend(
                [
                    product_image_in_db.preview_url,
                    product_image_in_db.mini_url,
                    product_image_in_db.small_url,
                ]
            )
            await self.session.delete(
                instance=product_image_in_db,
            )
        await self._multi_delete_files_to_s3(
            file_urls=images_delete,
            bucket=settings.s3_settings.bucket_public,
        )

    def _thumbnail_images(
        self,
        size_value: tuple[int, int],
        image_format: str,
        image_resize: OpenImage,
    ) -> BytesIO:
        """Изменяет масштаб изображения."""
        in_mem_resize_image = BytesIO()
        image_resize.thumbnail(size_value)
        image_resize.save(in_mem_resize_image, format=image_format)
        in_mem_resize_image.seek(0)
        return in_mem_resize_image

    async def _update_product_images(self, update_product_images: list[dict]) -> None:
        """Обновляет изображения продукта."""
        images_resize = []
        images_delete = []
        url = settings.s3_settings.url
        bucket_public = settings.s3_settings.bucket_public
        for update_product_image in update_product_images:
            product_image_in_db: ProductImageInDB = await self._get_one(
                statement=select(ProductImageInDB).where(
                    ProductImageInDB.id == update_product_image["id"],
                )
            )
            order_num = update_product_image["order_num"]
            image = update_product_image.get("image")
            if product_image_in_db.order_num == order_num and not image:
                continue
            product_image_in_db.order_num = order_num
            if image:
                image_resize = Image.open(BytesIO(image["file"]))
                image_format = image_resize.format.lower()
                old_image_format = product_image_in_db.preview_url.split(".")[-1]
                for size_title, size_value in image_sizes.items():
                    in_mem_resize_image = self._thumbnail_images(size_value, image_format, image_resize)
                    old_image_url: str = getattr(product_image_in_db, size_title)
                    storage_path = old_image_url.split("temp/")[1]
                    if image_format != old_image_format:
                        storage_path = f"products/images/{size_title}/{str(uuid4())}.{image_format.lower()}"
                        image_url = join(url, bucket_public, "temp", storage_path)
                        setattr(product_image_in_db, size_title, image_url)
                        images_delete.append(old_image_url)
                    images_resize.append(
                        FileObject(
                            storage_path=storage_path,
                            file_object=in_mem_resize_image,
                        )
                    )
            self.session.add(
                instance=product_image_in_db,
            )
        await self._multi_upload_files_to_s3(file_objects=images_resize, bucket=bucket_public)
        await self._multi_delete_files_to_s3(
            file_urls=images_delete,
            bucket=settings.s3_settings.bucket_public,
        )

    async def _create_product_images(
        self,
        create_product_images: list[dict],
        product_id: UUID,
    ) -> None:
        """Создаёт изображения продукта."""
        product_images = []
        images_resize = []
        url = settings.s3_settings.url
        bucket_public = settings.s3_settings.bucket_public
        for create_product_image in create_product_images:
            image = create_product_image["image"]
            image_resize = Image.open(BytesIO(image["file"]))
            image_format = image_resize.format
            data_product_image = {
                "order_num": create_product_image["order_num"],
                "product_id": product_id,
            }
            for size_title, size_value in image_sizes.items():
                in_mem_resize_image = self._thumbnail_images(size_value, image_format, image_resize)
                storage_path = f"products/images/{size_title}/{str(uuid4())}.{image_format.lower()}"
                data_product_image[size_title] = join(url, bucket_public, "temp", storage_path)
                images_resize.append(
                    FileObject(
                        storage_path=storage_path,
                        file_object=in_mem_resize_image,
                    )
                )
            product_images.append(ProductImageInDB(**data_product_image))
        await self._multi_upload_files_to_s3(file_objects=images_resize, bucket=bucket_public)
        self.session.add_all(
            instances=product_images,
        )

    async def _upload_product_images(
        self,
        product_in_db: ProductInDB,
        images: list[dict],
    ) -> None:
        """Обновляет изображения продукта."""
        list_link_fields = [(("id", ProductImageInDB, image.get("id")),) for image in images]
        await self._list_validation_link_fields(list_link_fields)
        product_images = product_in_db.images
        delete_product_images, update_product_images, create_product_images = self._get_delete_update_create_images(
            product_images, images
        )
        await self._create_product_images(create_product_images, product_in_db.id)
        await self._update_product_images(update_product_images)
        await self._delete_product_images(delete_product_images)

    async def _create_product_documents(
        self,
        create_product_documents: list[dict],
        product_id: UUID,
    ) -> None:
        """Создаёт документы продукта."""
        product_documents = []
        documents_objects = []
        bucket_private = settings.s3_settings.bucket_private
        for create_product_document in create_product_documents:
            document = create_product_document["document"]
            data_product_document = {
                "product_id": product_id,
            }
            file_format = document["file_format"].lower()
            storage_path = f"products/documents/{str(uuid4())}.{file_format}"
            data_product_document["key"] = join("temp", storage_path)
            data_product_document["extension"] = file_format
            data_product_document["name"] = create_product_document["name"]
            documents_objects.append(
                FileObject(
                    storage_path=storage_path,
                    file_object=BytesIO(document["file"]),
                )
            )
            product_documents.append(ProductDocumentInDB(**data_product_document))
        await self._multi_upload_files_to_s3(
            file_objects=documents_objects,
            bucket=bucket_private,
            public=False,
        )
        self.session.add_all(
            instances=product_documents,
        )

    async def _delete_product_documents(self, delete_product_documents: list[UUID]) -> None:
        """Удаляет документы продукта."""
        product_documents_in_db: list[ProductDocumentInDB] = await self._get_all(
            statement=select(ProductDocumentInDB).where(
                ProductDocumentInDB.id.in_(delete_product_documents),
            ),
            count=1,
        )
        documents_delete = []
        for product_document_in_db in product_documents_in_db:
            documents_delete.append(product_document_in_db.key)
            await self.session.delete(
                instance=product_document_in_db,
            )
        await self._multi_delete_files_to_s3(
            file_urls=documents_delete,
            bucket=settings.s3_settings.bucket_private,
        )

    def _get_delete_create_documents(
        self,
        product_documents: list[ProductDocumentInDB],
        documents: list[dict],
    ) -> tuple[list[UUID], list[dict]]:
        """Отдаёт документы для удаления и создания."""
        product_documents_id = {product_document.id: product_document.id for product_document in product_documents}
        create_product_documents = []
        list_errors = []
        for document in documents:
            document_id = document.get("id")
            if not document_id:
                create_product_documents.append(document)
                continue
            if document_id not in product_documents_id:
                list_errors.append({"id": self.does_not_exist_message.format(document_id)})
                continue
            product_documents_id.pop(document_id)
        if list_errors:
            raise HTTPException(status_code=422, detail=list_errors)
        delete_product_documents = product_documents_id.keys()
        return delete_product_documents, create_product_documents

    async def _upload_product_documents(
        self,
        product_in_db: ProductInDB,
        documents: list[dict],
    ) -> None:
        """Обновляет документы продукта."""
        list_link_fields = [(("id", ProductDocumentInDB, document.get("id")),) for document in documents]
        await self._list_validation_link_fields(list_link_fields)
        product_documents = product_in_db.documents
        delete_product_documents, create_product_documents = self._get_delete_create_documents(
            product_documents,
            documents,
        )
        await self._create_product_documents(create_product_documents, product_in_db.id)
        await self._delete_product_documents(delete_product_documents)

    async def create_product(
        self,
        seller_id: UUID,
        product: ProductCreate,
    ) -> ProductInDB:
        product_dict_without_nested_schemas: dict[str:Any] = jsonable_encoder(
            product,
            exclude={"images", "manually_filled_specification", "pack", "price", "documents", "messages"},
            exclude_unset=True,
        )
        link_fields = (
            ("subcategory_id", ProductSubCategoryInDB, product_dict_without_nested_schemas.get("subcategory_id")),
            ("color_id", ProductColorInDB, product_dict_without_nested_schemas.get("color_id")),
            ("size_id", ProductSizeInDB, product_dict_without_nested_schemas.get("size_id")),
        )
        await self._validation_link_fields(link_fields)
        product_dict_without_nested_schemas = product_dict_without_nested_schemas | {
            "seller_id": seller_id,
            "name_slug": slugify(
                f"{product.name}-{uuid4()}",
                max_length=255,
            ),
        }
        product_in_db = ProductInDB(**product_dict_without_nested_schemas)
        self.session.add(product_in_db)

        product_in_db.manually_filled_specification = ProductManuallyFilledSpecificationInDB(
            **product.manually_filled_specification.model_dump()
        )
        product_in_db.pack = ProductPackInDB(**product.pack.model_dump())
        product_in_db.price = ProductPriceInDB(**product.price.model_dump())

        images = product.images
        documents = product.documents
        if images:
            images = [image.model_dump() for image in images]
            self._validation_order_num([image["order_num"] for image in images])
            await self._create_product_images(images, product_in_db.id)
        if documents:
            documents = [document.model_dump() for document in documents]
            await self._create_product_documents(documents, product_in_db.id)

        try:
            await self.session.commit()
            await self.session.refresh(product_in_db)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"{exc}")

        return product_in_db

    async def get_document(
        self,
        document_id: UUID,
        seller_id: UUID,
    ) -> Response:
        """Отдаёт документ по продукту."""
        document_in_db: ProductDocumentInDB = await self._get_one(
            select(ProductDocumentInDB)
            .options(joinedload(ProductDocumentInDB.product))
            .where(
                ProductDocumentInDB.id == document_id,
            ),
        )
        self._check_access_to_product(document_in_db.product, seller_id)
        bucket_private = settings.s3_settings.bucket_private
        file = await self._get_file_in_s3(document_in_db.key, bucket_private)
        return Response(content=file["Body"].read(), status_code=status.HTTP_200_OK)

    async def delete(
        self,
        seller_id: UUID,
        product_id: UUID,
    ) -> Response:
        # FIXME: Не работает. Необходимо переделать реализацию.
        product_in_db: ProductInDB = await self._get_one(
            statement=select(ProductInDB).where(
                ProductInDB.seller_id == seller_id,
                ProductInDB.id == product_id,
            )
        )
        self._check_access_to_product(product_in_db, seller_id)
        await self.session.delete(
            instance=product_in_db,
        )
        await self.session.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    async def get_products_by_ids(
        self,
        product_ids: list[UUID],
    ) -> list[ProductInDB]:
        products_in_db: list[ProductInDB] = await self._get_all(
            statement=select(ProductInDB).where(
                ProductInDB.id.in_(product_ids),
            ),
            count=len(product_ids),
        )
        return products_in_db

    async def get_one(
        self,
        product_slug: str,
    ) -> ProductInDB:
        product_in_db: ProductInDB = await self._get_one(
            statement=select(ProductInDB).where(
                ProductInDB.name_slug == product_slug,
            )
        )
        return product_in_db

    async def get_name_by_id(
        self, product_id: UUID, request_info: RequestInfo, background_tasks: BackgroundTasks
    ) -> ReadProductName:
        product_in_db: ProductInDB = await self._get_one(
            statement=select(ProductInDB).where(
                ProductInDB.id == product_id,
            )
        )
        return product_in_db

    def _product_validate(self, product_in_db: ProductInDB) -> ProductRead:
        """Валидация продукта."""
        return ProductRead.model_validate(
            obj={
                **product_in_db.model_dump(),
                "pack": {**product_in_db.pack.model_dump()},
                "manually_filled_specification": {**product_in_db.manually_filled_specification.model_dump()},
                "price": {**product_in_db.price.model_dump()},
                "images": [image.model_dump() for image in product_in_db.images],
                "documents": [document.model_dump() for document in product_in_db.documents],
            }
        )

    async def get_all(self, seller_id: UUID, page: int, size: int) -> ProductPagination:
        total_count: int = await self._get_count(
            select(func.count())
            .select_from(ProductInDB)
            .where(
                ProductInDB.seller_id == seller_id,
            )
        )

        if total_count == 0:
            return ProductPagination(page=page, size=size, total_count=total_count, results=[])
        total_pages: int = ceil(total_count / size)
        page = total_pages if page > total_pages else page

        products_in_db: list[ProductInDB] = await self._get_all(
            count=total_count,
            statement=select(ProductInDB)
            .limit(size)
            .offset((page - 1) * size)
            .where(
                ProductInDB.seller_id == seller_id,
            ),
        )
        products = [self._product_validate(product_in_db) for product_in_db in products_in_db]

        return ProductPagination(
            page=page, size=size, total_count=total_count, total_pages=total_pages, results=products
        )

    async def get_all_sizes(
        self,
    ) -> list[dict[str, Any]]:
        coroutine = self._get_all(count=1, statement=select(ProductSizeInDB))
        return await self._get_data_in_cache_or_db(coroutine, "sizes")

    async def get_all_colors(
        self,
    ) -> list[dict[str, Any]]:
        coroutine = self._get_all(count=1, statement=select(ProductColorInDB))
        return await self._get_data_in_cache_or_db(coroutine, "colors")

    async def get_all_brands(
        self,
    ) -> list[dict[str, Any]]:
        coroutine = self._get_all(count=1, statement=select(ProductBrandInDB))
        return await self._get_data_in_cache_or_db(coroutine, "brands")

    async def get_all_categories_and_subcategories(
        self,
    ) -> list[dict[str, Any]]:
        """Получение списка категорий с подкатегориями."""
        coroutine = self._get_all(
            count=1,
            statement=select(ProductCategoryInDB),
        )
        return await self._get_data_in_cache_or_db(
            coroutine,
            "categories_and_subcategories",
            ["subcategories"],
        )

    async def delete_all(
        self,
        seller_id: str,
    ) -> Response:
        # FIXME: Не работает. Необходимо переделать реализацию.
        await self._delete_all(
            statement=select(
                ProductInDB,
            ).where(
                ProductInDB.seller_id == seller_id,
            )
        )

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    def _update_values_to_fields_model_object(self, obj: SQLModel, values: dict[str, Any]) -> None:
        """Обновляет значения полям объекта модели."""
        for field_name, field_value in values.items():
            setattr(obj, field_name, field_value)

    async def _update_values_to_objects_link_product(
        self,
        data_objects: tuple[tuple[SQLModel, dict[str, Any]]],
        product_id: UUID,
    ) -> None:
        """Обновляет значения объектам, ссылающие на продукт."""
        for model, values in data_objects:
            if not values:
                continue
            obj_in_db: SQLModel = await self._get_one(
                statement=select(
                    model,
                ).where(
                    model.product_id == product_id,
                )
            )
            self._update_values_to_fields_model_object(obj_in_db, values)

    async def _update_values_to_product(
        self,
        product_id: UUID,
        seller_id: UUID,
        data: dict[str, Any],
    ) -> ProductInDB:
        """Обновляет значения продукта."""
        product_in_db: ProductInDB = await self._get_one(
            statement=select(
                ProductInDB,
            ).where(
                ProductInDB.id == product_id,
            )
        )
        self._check_access_to_product(product_in_db, seller_id)
        link_fields = (
            ("subcategory_id", ProductSubCategoryInDB, data.get("subcategory_id")),
            ("color_id", ProductColorInDB, data.get("color_id")),
            ("size_id", ProductSizeInDB, data.get("size_id")),
        )
        await self._validation_link_fields(link_fields)
        self._update_values_to_fields_model_object(product_in_db, data)
        name = data.get("name")
        if name is None:
            return product_in_db
        product_in_db.name_slug = slugify(
            f"{str(name)}-{uuid4()}",
            max_length=255,
        )
        return product_in_db

    async def edit(
        self,
        seller_id: UUID,
        product_id: UUID,
        product: ProductUpdate,
    ) -> ProductInDB:
        product: dict[str, Any] = product.model_dump(exclude_unset=True)
        data_objects_link_product = (
            (ProductPriceInDB, product.pop("price", None)),
            (ProductPackInDB, product.pop("pack", None)),
            (ProductManuallyFilledSpecificationInDB, product.pop("manually_filled_specification", None)),
        )
        images = product.pop("images", None)
        documents = product.pop("documents", None)
        product_in_db = await self._update_values_to_product(product_id, seller_id, product)
        await self._update_values_to_objects_link_product(data_objects_link_product, product_id)
        if documents is not None:
            await self._upload_product_documents(product_in_db, documents)
        if images is not None:
            await self._upload_product_images(product_in_db, images)

        self.session.add(instance=product_in_db)
        await self.session.commit()
        await self.session.refresh(instance=product_in_db)
        return product_in_db

    async def get_products_prices(
        self,
        product_ids: list[UUID],
    ) -> list[ProductPriceInDB]:
        prices_in_db: ProductPriceInDB = await self._get_all(
            statement=select(ProductPriceInDB).where(
                ProductPriceInDB.product_id.in_(product_ids),
            ),
            count=len(product_ids),
        )
        return prices_in_db

    async def change_product_status(
        self, product_id: UUID, seller_id: UUID, user_token: str, product_status: ProductStatusForChange
    ) -> Response:
        """Изменяет статус товара и
        отправляет массив данных о товаре в очередь RabbitMQ для сервиса ETL_Products
        Args:
            product_id (UUID): id товара
            seller_id (UUID): id продавца
            user_token (str): токен пользователя
            product_status (ProductStatusForChange): статус товара
        Raises:
            HTTPException: если не прошла проверка на возможность изменения статуса
            при текущем статусе товара
        Returns:
            Response: статус-код 200 (запрос выполнен)
        """
        product_in_db: ProductInDB = await self._get_one(
            statement=select(ProductInDB).where(ProductInDB.id == product_id, ProductInDB.seller_id == seller_id)
        )
        product_in_db.is_active = False
        match product_status, product_in_db.status:
            case ProductStatusForChange.on_sale, ProductStatus.ready_for_sale:
                product_info: dict[str, Any] = await self.create_product_info_for_ETL(
                    product_in_db=product_in_db, user_token=user_token
                )
                await self.rabbit_mq.send_message(body=orjson.dumps(product_info), routing_key="products.updated")
                product_in_db.status = product_status
                product_in_db.is_active = True
            case ProductStatusForChange.not_for_sale, ProductStatus.on_sale:
                await self.rabbit_mq.send_message(
                    body=orjson.dumps({"id": str(product_id), "is_active": False}), routing_key="products.updated"
                )
                product_in_db.status = product_status
            case (ProductStatusForChange.on_moderation, ProductStatus.new | ProductStatus.needs_fix):
                product_in_db.status = product_status
            case ProductStatusForChange.deleted, ProductStatus.on_sale:
                await self.rabbit_mq.send_message(
                    body=orjson.dumps({"id": str(product_id), "is_active": False}), routing_key="products.updated"
                )
                product_in_db.status = product_status
            case (
                ProductStatusForChange.deleted,
                ProductStatus.new
                | ProductStatus.on_moderation
                | ProductStatus.ready_for_sale
                | ProductStatus.needs_fix
                | ProductStatus.not_for_sale,
            ):
                product_in_db.status = product_status
            case _:
                raise HTTPException(
                    status_code=status.HTTP_406_NOT_ACCEPTABLE,
                    detail=(
                        "Невозможно установить данный статус при текущем статусе продукта"
                        f" ({product_in_db.status.value})"
                    ),
                )

        self.session.add(product_in_db)
        await self.session.commit()
        await self.session.refresh(product_in_db)
        return Response()

    async def _get_seller_data(self, user_token: str) -> dict[str, Any]:
        """Получет данные о продавце от сервиса личного кабинета продавца (Sellers)
        Args:
            user_token (str): токен пользователя
        Raises:
            HTTPException: при невалидности полученных данных
        Returns:
           dict[str, Any]: валидные данные о продавце в json-сериализируемом формате
        """
        seller_data_response: dict[str, Any] = await self._get_response_from_external_service(
            service_url=settings.ecom_settings.seller_data_url, headers={"Authorization": f"Bearer {user_token}"}
        )
        try:
            seller_data: dict[str, Any] = SellerData.model_validate(
                obj={
                    **seller_data_response.get("registration_data"),
                    **seller_data_response,
                }
            ).model_dump(mode="json")
            return seller_data
        except Exception as err:
            raise HTTPException(status_code=502, detail=f"Ошибка в получении данных о продавце товара: {err}")

    async def _get_product_storage_quantity(self, product_id: UUID) -> int:
        """Получет данные о количестве товара от сервиса складов ("Storages")
        Args:
            product_id (UUID): id товара
        Raises:
            HTTPException: при невалидности полученных данных

        Returns:
            int: количество товара в штуках
        """
        product_storage_quantity_response: list[dict[str, Any]] = await self._get_response_from_external_service(
            service_url=settings.ecom_settings.product_storage_amount_url, method="POST", json=[str(product_id)]
        )
        if not product_storage_quantity_response:
            return 0
        else:
            try:
                return ProductStorageQuantity.model_validate(product_storage_quantity_response[0]).storage_quantity
            except Exception as err:
                raise HTTPException(
                    status_code=502, detail=f"Ошибка в получении данных о количестве товара на складе: {err}"
                )

    async def create_product_info_for_ETL(
        self,
        product_in_db: ProductInDB,
        user_token: str,
    ) -> dict[str, Any]:
        """Создаёт массив данных о товаре для отправки в очередь RabbitMQ для сервиса ETL_Products

        Args:
            product_in_db (ProductInDB): инстанс товара из базы данных
            user_token (str): токен пользователя

        Returns:
            dict[str, Any]: массив данных о товаре в json-сериализируемом формате
        """
        seller_data: dict[str, Any] = await self._get_seller_data(user_token=user_token)
        storage_quantity_data: int = await self._get_product_storage_quantity(product_id=product_in_db.id)
        fields_to_exclude = ["products", "created_at", "updated_at", "category_id"]
        subcategory_in_db: ProductSubCategoryInDB = product_in_db.subcategory
        category_in_db: ProductCategoryInDB = await self._get_one(
            statement=select(ProductCategoryInDB).where(ProductCategoryInDB.id == subcategory_in_db.category_id)
        )
        product_data_schema: ProductForElastic = ProductForElastic.model_validate(product_in_db, from_attributes=True)
        product_data_schema.is_active = True
        product_data: dict[str, Any] = product_data_schema.model_dump(
            exclude=[
                "subcategory_id",
                "status",
                "brand_id",
                "color_id",
                "size_id",
            ],
            exclude_none=True,
            exclude_unset=True,
            mode="json",
        )

        product_info: dict[str, Any] = {
            "seller": {**seller_data},
            "storage_quantity": storage_quantity_data,
            "category": {**category_in_db.model_dump(exclude=fields_to_exclude, mode="json")},
            **product_data,
        }
        return product_info


@lru_cache
def get_service(
    session: AsyncSession = Depends(dependency=get_session),
    cache: Cache = Depends(dependency=get_cache),
    rabbit_mq: RabbitMQ = Depends(dependency=get_rabbitmq),
) -> Service:
    return Service(session=session, cache=cache, rabbit_mq=rabbit_mq)
