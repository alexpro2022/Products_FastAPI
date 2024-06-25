from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from app.models.fields_extensions_models import GenderType, ProductStatus
from app.schemas.base import PaginationBase
from app.schemas.categories_schemas import ProductSubCategory
from app.schemas.fields_extensions_schemas import (
    ProductBrand,
    ProductColor,
    ProductDocument,
    ProductDocumentCreate,
    ProductDocumentUpdate,
    ProductImage,
    ProductImageCreate,
    ProductImageUpdate,
    ProductManuallyFilledSpecification,
    ProductManuallyFilledSpecificationUpdate,
    ProductMessage,
    ProductPack,
    ProductPackUpdate,
    ProductPrice,
    ProductPriceUpdate,
    ProductSize,
)


class ProductBase(BaseModel):
    """Базовая схема продукта."""

    gender: GenderType | None = Field(
        default=None,
        description="Пол",
    )
    name: str = Field(
        max_length=128,
        description="Наименование товара",
    )
    vendor_code: str = Field(
        max_length=255,
        description="Артикул товара",
    )
    barcode: int = Field(
        description="Штрихкод товара",
    )
    country_of_manufacture: str = Field(
        max_length=255,
        description="Страна производства товара",
    )
    size_id: UUID | None = Field(
        default=None,
        description="ID размера",
    )
    brand_id: UUID | None = Field(
        default=None,
        description="ID бренда",
    )
    color_id: UUID | None = Field(
        description="ID цвета",
        default=None,
    )
    subcategory_id: UUID = Field(
        description="ID подкатегории",
    )
    pack: ProductPack = Field(
        description="Характеристики упаковки товара",
    )
    manually_filled_specification: ProductManuallyFilledSpecification = Field(
        description="Характеристики товара, заполняемые вручную",
    )
    price: ProductPrice = Field(
        description="Информация о цене товара",
    )


class ProductCreate(ProductBase):
    """Схема создания продукта."""

    images: list[ProductImageCreate] | None = Field(
        default=None,
        description="Изображения товара в base64 строке",
    )
    documents: list[ProductDocumentCreate] | None = Field(
        default=None,
        description="Документы товара в base64 строке",
    )

    model_config = {
        "title": "Создание товара",
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Платье повседневное мини оверсайз",
                    "country_of_manufacture": "КНР",
                    "vendor_code": "EPE0123",
                    "barcode": "123456789",
                    "subcategory_id": str(uuid4()),
                    "manually_filled_specification": ProductManuallyFilledSpecification.model_json_schema()["examples"][
                        0
                    ],
                    "pack": ProductPack.model_json_schema()["examples"][0],
                    "gender": GenderType.female,
                    "color_id": str(uuid4()),
                    "size_id": str(uuid4()),
                    "brand_id": str(uuid4()),
                    "price": ProductPrice.model_json_schema()["examples"][0],
                    "images": [ProductImageCreate.model_json_schema()["examples"][0]],
                    "documents": [ProductDocumentCreate.model_json_schema()["examples"][0]],
                }
            ]
        },
    }


class ProductReadNotСonfidential(ProductBase):
    """Схема чтения продукта без конфиденциальной информации."""

    id: UUID = Field(
        description="ID товара",
    )
    is_active: bool = Field(
        description="Активность товара",
    )
    status: ProductStatus = Field(default=ProductStatus.new, description="Статус товара")
    name_slug: str = Field(
        max_length=255,
        description="URL товара",
    )
    images: list[ProductImage] | None = Field(
        default=None,
        description="Информация об изображениях товара",
    )
    model_config = {
        "title": "Информация о товаре",
        "json_schema_extra": {
            "examples": [
                {
                    "id": str(uuid4()),
                    "is_active": False,
                    "status": ProductStatus.new,
                    "name": "Платье повседневное мини оверсайз",
                    "name_slug": f"Платье повседневное мини оверсайз-{str(uuid4())}",
                    "country_of_manufacture": "КНР",
                    "vendor_code": "EPE0123",
                    "barcode": "123456789",
                    "subcategory_id": str(uuid4()),
                    "manually_filled_specification": ProductManuallyFilledSpecification.model_json_schema()["examples"][
                        0
                    ],
                    "pack": ProductPack.model_json_schema()["examples"][0],
                    "gender": GenderType.female,
                    "color_id": str(uuid4()),
                    "size_id": str(uuid4()),
                    "brand_id": str(uuid4()),
                    "price": ProductPrice.model_json_schema()["examples"][0],
                    "images": [ProductImage.model_json_schema()["examples"][0]],
                }
            ]
        },
    }


class ProductForElastic(ProductReadNotСonfidential):
    """Схема товара для отправки в Elastic Search"""

    size: ProductSize | None
    brand: ProductBrand | None
    color: ProductColor | None
    subcategory: ProductSubCategory

    model_config = {
        "title": "Информация о товаре для отправки в Elastic Search",
        "json_schema_extra": {
            "examples": [
                {
                    **ProductReadNotСonfidential.model_json_schema()["examples"][0],
                    "size": ProductSize.model_json_schema()["examples"][0],
                    "brand": ProductBrand.model_json_schema()["examples"][0],
                    "color": ProductColor.model_json_schema()["examples"][0],
                    "subcategory": ProductSubCategory.model_json_schema()["examples"][0],
                }
            ]
        },
    }


class ProductRead(ProductReadNotСonfidential):
    """Схема чтения продукта."""

    external_id: str | None = Field(
        default=None,
        description="ID товара в учётной системе продавца",
    )
    documents: list[ProductDocument] | None = Field(
        default=None,
        description="Информация о документах товара",
    )
    messages: list[ProductMessage] | None = Field(default=None, description="Cообщения о модерации продукта")
    model_config = {
        "title": "Информация о товаре",
        "json_schema_extra": {
            "examples": [
                {
                    "id": str(uuid4()),
                    "is_active": False,
                    "status": ProductStatus.new,
                    "name": "Платье повседневное мини оверсайз",
                    "name_slug": f"Платье повседневное мини оверсайз-{str(uuid4())}",
                    "country_of_manufacture": "КНР",
                    "vendor_code": "EPE0123",
                    "barcode": "123456789",
                    "subcategory_id": str(uuid4()),
                    "manually_filled_specification": ProductManuallyFilledSpecification.model_json_schema()["examples"][
                        0
                    ],
                    "pack": ProductPack.model_json_schema()["examples"][0],
                    "gender": GenderType.female,
                    "color_id": str(uuid4()),
                    "size_id": str(uuid4()),
                    "brand_id": str(uuid4()),
                    "price": ProductPrice.model_json_schema()["examples"][0],
                    "documents": [ProductDocument.model_json_schema()["examples"][0]],
                    "images": [ProductImage.model_json_schema()["examples"][0]],
                    "messages": [ProductMessage.model_json_schema()["examples"][0]],
                }
            ]
        },
    }


class ProductUpdate(ProductBase):
    """Схема обновления продукта."""

    name: str | None = Field(
        default=None,
        max_length=128,
        description="Наименование товара",
    )
    country_of_manufacture: str | None = Field(
        default=None,
        max_length=255,
        description="Страна производства товара",
    )
    vendor_code: str | None = Field(
        default=None,
        max_length=255,
        description="Артикул товара",
    )
    barcode: int | None = Field(
        default=None,
        description="Штрихкод товара",
    )
    subcategory_id: UUID | None = Field(
        default=None,
        description="ID подкатегории",
    )
    pack: ProductPackUpdate | None = Field(
        default=None,
        description="Характеристики упаковки товара",
    )
    price: ProductPriceUpdate | None = Field(
        default=None,
        description="Информация о цене товара",
    )
    manually_filled_specification: ProductManuallyFilledSpecificationUpdate | None = Field(
        default=None,
        description="Характеристики товара, заполняемые вручную",
    )
    images: list[ProductImageUpdate] | None = Field(
        default=None,
        description="Изображения товара в base64 строке",
    )
    documents: list[ProductDocumentUpdate] | None = Field(
        default=None,
        description="Документы товара в base64 строке",
    )
    model_config = {
        "title": "Обновление товара",
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Платье повседневное мини оверсайз",
                    "country_of_manufacture": "КНР",
                    "vendor_code": "EPE0123",
                    "barcode": "123456789",
                    "subcategory_id": str(uuid4()),
                    "gender": GenderType.female,
                    "color_id": str(uuid4()),
                    "size_id": str(uuid4()),
                    "price": ProductPriceUpdate.model_json_schema()["examples"][0],
                    "pack": ProductPackUpdate.model_json_schema()["examples"][0],
                    "manually_filled_specification": ProductManuallyFilledSpecification.model_json_schema()["examples"][
                        0
                    ],
                    "images": ProductImageUpdate.model_json_schema()["examples"][0],
                    "documents": ProductDocumentUpdate.model_json_schema()["examples"][0],
                }
            ]
        },
    }

    @field_validator(
        "name",
        "country_of_manufacture",
        "vendor_code",
        "barcode",
        "subcategory_id",
        "manually_filled_specification",
        "pack",
        "price",
        "images",
        "documents",
    )
    @classmethod
    def validation_for_null(cls, value: Any) -> Any:
        """Валидация полей на null значение."""
        if value is None:
            raise ValueError("The field cannot be null.")
        return value


class ReadProductName(BaseModel):
    name: str = Field(
        description="Наименование продукта",
    )
    model_config = {"title": "Наименование продукта", "json_schema_extra": {"example": [{"name": "Lenovo laptop"}]}}


class ProductPagination(PaginationBase):
    results: list[ProductRead] = Field(
        description="""
        Товары продавца
        """
    )

    model_config = {
        "title": "Получения продуктов с пагинацией",
        "json_schema_extra": {
            "example": [
                {
                    **PaginationBase.model_json_schema()["examples"][0],
                    "results": [ProductRead.model_json_schema()["examples"]],
                }
            ]
        },
    }
