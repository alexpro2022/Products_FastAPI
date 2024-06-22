from io import BytesIO
from tempfile import SpooledTemporaryFile
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import Self

from app.models.fields_extensions_models import SizeGroup, ValueAddedTax, default_image_url
from app.schemas.castom_types import DocumentBase64File, ImageBase64File


class FileObject(BaseModel):
    storage_path: str = Field(description="Путь к файлу в хранилище")
    file_object: BytesIO | SpooledTemporaryFile = Field(description="Поток байтов файла в памяти")

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ProductImageBase(BaseModel):
    """Базовая схема изображения продукта."""

    id: UUID | None = Field(
        default=None,
        description="ID изображения продукта",
    )
    order_num: int = Field(description="Порядковый номер изображения")


class ProductImage(ProductImageBase):
    """Схема вывода изображения продукта."""

    preview_url: str = Field(description="URL превью изображения товара", default=default_image_url)
    mini_url: str = Field(description="URL изображения товара маленького размера", default=default_image_url)
    small_url: str = Field(description="URL изображения товара среднего размера", default=default_image_url)
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": str(uuid4()),
                    "image_preview": default_image_url,
                    "image_mini": default_image_url,
                    "image_small": default_image_url,
                    "order_num": 0,
                }
            ]
        }
    }


class ProductImageCreate(BaseModel):
    """Схема создания изображения продукта."""

    image: ImageBase64File = Field(description="Изображение в base64 кодировке")
    order_num: int = Field(description="Порядковый номер изображения")
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
                    "order_num": 0,
                }
            ]
        }
    }


class ProductImageUpdate(ProductImageBase):
    """Схема обновления изображения продукта."""

    image: ImageBase64File | None = Field(default=None, description="Изображение в base64 кодировке")
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": str(uuid4()),
                    "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
                    "order_num": 0,
                }
            ]
        }
    }

    @model_validator(mode="after")
    def validation_presence_image_or_id(self) -> Self:
        if not any((self.image, self.id)):
            raise ValueError("the image and id cannot be missing at the same time")
        return self


class ProductDocumentBase(BaseModel):
    """Базовая схема документа продукта."""

    name: str | None = Field(
        default=None,
        description="Имя документа",
    )
    id: UUID | None = Field(
        default=None,
        description="ID документа продукта",
    )


class ProductDocument(ProductDocumentBase):
    """Схема вывода документа продукта."""

    extension: str = Field(
        description="Расширение документа",
    )
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": str(uuid4()),
                    "name": "document",
                    "extension": "pdf",
                }
            ]
        }
    }


class ProductDocumentCreate(BaseModel):
    """Схема создания документа продукта."""

    name: str = Field(
        description="Имя документа",
    )
    document: DocumentBase64File = Field(description="Документ в base64 кодировке")
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "document",
                    "document": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
                }
            ]
        }
    }


class ProductMessage(BaseModel):
    message: str = Field(
        description="Сообщение",
    )
    is_active: bool = Field(
        description="Статус сообщения",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "message",
                    "is_active": True,
                }
            ]
        }
    }


class ProductDocumentUpdate(ProductDocumentBase):
    """Схема обновления документа продукта."""

    document: DocumentBase64File | None = Field(
        default=None,
        description="Документ в base64 кодировке",
    )
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": str(uuid4()),
                    "name": "document",
                    "document": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
                }
            ]
        }
    }

    @model_validator(mode="after")
    def validation_presence_document_or_id(self) -> Self:
        if not any((self.document, self.id)):
            raise ValueError("the document and id cannot be missing at the same time")
        elif self.document and not self.name:
            raise ValueError("the name is a required field")
        return self


class ProductPackBase(BaseModel):
    """Базовая схема габаритов упаковки продукта."""

    model_config = {"json_schema_extra": {"examples": [{"length": 10, "width": 5, "height": 8, "weight_packed": 100}]}}


class ProductPack(ProductPackBase):
    """Схема габаритов упаковки продукта."""

    length: int = Field(ge=1, description="Длина упаковки, мм")
    width: int = Field(ge=1, description="Ширина упаковки, мм")
    height: int = Field(ge=1, description="Высота упаковки, мм")
    weight_packed: int = Field(ge=1, description="Вес упаковки, г")


class ProductPackUpdate(ProductPackBase):
    """Схема обновления габаритов упаковки продукта."""

    length: int | None = Field(
        default=None,
        ge=1,
        description="Длина упаковки, мм",
    )
    width: int | None = Field(
        default=None,
        ge=1,
        description="Ширина упаковки, мм",
    )
    height: int | None = Field(
        default=None,
        ge=1,
        description="Высота упаковки, мм",
    )
    weight_packed: int | None = Field(
        default=None,
        ge=1,
        description="Вес упаковки, г",
    )

    @field_validator(
        "length",
        "width",
        "height",
        "weight_packed",
    )
    @classmethod
    def validation_for_null(cls, value: Any) -> Any:
        """Валидация полей на null значение."""
        if value is None:
            raise ValueError("The field cannot be null.")
        return value


class ProductManuallyFilledSpecificationBase(BaseModel):
    """Базовая схема спецификации продукта."""

    custom_properties: dict[str, str] | None = Field(
        default=None,
        description="Характеристики товара, добавляемые продавцом самостоятельно",
    )
    description: str | None = Field(default=None, description="Описание товара")
    weight: int | None = Field(
        default=None,
        ge=1,
        description="Вес товара (нетто), г",
    )
    length: int | None = Field(
        default=None,
        ge=1,
        description="Длина товара в собранном виде, мм",
    )
    width: int | None = Field(
        default=None,
        ge=1,
        description="Ширина товара в собранном виде, мм",
    )
    height: int | None = Field(
        default=None,
        ge=1,
        description="Высота товара в собранном виде, мм",
    )
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "Платье трикотажкое",
                    "custom_properties": {"характеристика 1": "Состав: 92% Хлопок 8% Эластан"},
                    "weight": 100,
                    "length": 100,
                    "width": 100,
                    "height": 100,
                    "description": "Лучшее платье",
                }
            ]
        }
    }


class ProductManuallyFilledSpecification(ProductManuallyFilledSpecificationBase):
    """Cхема спецификации продукта."""

    type: str = Field(
        description="Тип товара",
    )


class ProductManuallyFilledSpecificationUpdate(ProductManuallyFilledSpecificationBase):
    """Cхема спецификации продукта."""

    type: str | None = Field(
        default=None,
        description="Тип товара",
    )

    @field_validator("type")
    @classmethod
    def validation_for_null(cls, value: Any) -> Any:
        """Валидация полей на null значение."""
        if value is None:
            raise ValueError("The field cannot be null.")
        return value


class ProductPriceBase(BaseModel):
    """Базовая схема цены продукта."""

    price_without_discount: float | None = Field(
        default=None,
        gt=0,
        description="Цена товара без учета скидки, руб.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "price_with_discount": 99.99,
                    "price_without_discount": 119.99,
                    "vat": ValueAddedTax.twenty,
                }
            ]
        }
    }


class ProductPrice(ProductPriceBase):
    """Схема цены продукта."""

    price_with_discount: float = Field(
        gt=0,
        description="Цена товара c учётом скидки, руб.",
    )
    vat: ValueAddedTax = Field(
        description="Размер НДС",
    )


class ProductPriceUpdate(ProductPriceBase):
    """Схема обновления цены продукта."""

    price_with_discount: float | None = Field(
        default=None,
        gt=0,
        description="Цена товара c учётом скидки, руб.",
    )
    vat: ValueAddedTax | None = Field(
        default=None,
        description="Размер НДС",
    )

    @field_validator("price_with_discount", "vat")
    @classmethod
    def validation_for_null(cls, value: Any) -> Any:
        """Валидация полей на null значение."""
        if value is None:
            raise ValueError("The field cannot be null.")
        return value


class ProductSize(BaseModel):
    """Схема размера товара."""

    id: UUID = Field(description="ID размера товара")
    group_name: SizeGroup = Field(description="Название группы размеров на русском языке.")
    value: str = Field(description="Размер")
    model_config = {
        "title": "Получение размеров",
        "json_schema_extra": {
            "examples": [
                {
                    "id": str(uuid4()),
                    "group_name": SizeGroup.adult,
                    "value": "34",
                }
            ]
        },
    }


class ProductColor(BaseModel):
    """Схема цвета товара."""

    id: UUID = Field(description="ID цвета товара")
    name: str = Field(description="Название цвета на русском языке")
    html_code: str = Field(description="HTML-код цвета")
    model_config = {
        "title": "Получение цветов",
        "json_schema_extra": {
            "examples": [
                {
                    "id": str(uuid4()),
                    "name": "серый",
                    "html_code": "AFAFAF",
                }
            ]
        },
    }


class ProductBrand(BaseModel):
    """Схема бренда товара."""

    id: UUID = Field(description="ID бренда товара")
    name: str = Field(description="Название бренда")
    model_config = {
        "title": "Получение брендов",
        "json_schema_extra": {"examples": [{"id": str(uuid4()), "name": "Antonio Banderas"}]},
    }
