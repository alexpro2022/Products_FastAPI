from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, ClassVar
from uuid import UUID

from pydantic import ConfigDict
from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import ENUM as psEnum
from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Field, Relationship

from app.core.config import default_image_url
from app.db import metadata
from app.models.base import IDMixin, TimestampsMixin

if TYPE_CHECKING:
    from app.models.products_models import ProductInDB


class ValueAddedTax(str, Enum):
    not_taxed = "Не облагается"
    null = "0%"
    ten = "10%"
    twenty = "20%"


class SizeGroup(str, Enum):
    children = "Детские размеры"
    adult = "Взрослые размеры"


class GenderType(str, Enum):
    male = "Мужской"
    female = "Женский"


class ProductStatusForChange(str, Enum):
    """Статусы товара, доступные к изменению продавцом самостоятельно"""

    on_sale = "Продаётся"
    not_for_sale = "Снят с продажи"
    on_moderation = "На модерации"
    deleted = "Удалён"


class ProductStatus(str, Enum):
    """Полный набор статусов товара"""

    on_sale = "Продаётся"
    not_for_sale = "Снят с продажи"
    on_moderation = "На модерации"
    new = "Новый"
    ready_for_sale = "Готов к продаже"
    needs_fix = "Требуется доработка"
    deleted = "Удалён"


class ProductImageInDB(IDMixin, TimestampsMixin, table=True):
    """Изображение товара в БД"""

    __tablename__: ClassVar[str | Callable[..., str]] = "image"
    __table_args__: tuple = {"schema": metadata.schema}
    preview_url: str = Field(
        description="URL превью изображения товара", sa_column=Column(String, nullable=False, default=default_image_url)
    )
    mini_url: str = Field(
        description="URL изображения товара маленького размера",
        sa_column=Column(String, nullable=False, default=default_image_url),
    )
    small_url: str = Field(
        description="URL изображения товара среднего размера",
        sa_column=Column(String, nullable=False, default=default_image_url),
    )
    order_num: int = Field(
        description="Порядковый номер изображения",
        sa_column=Column(
            Integer,
            default=0,
        ),
    )
    product_id: UUID = Field(
        description="ID товара",
        sa_column=Column(
            Uuid,
            ForeignKey(f"{metadata.schema}.product.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    product: "ProductInDB" = Relationship(
        back_populates="images",
        sa_relationship=RelationshipProperty(back_populates="images", uselist=False, single_parent=True),
    )


class ProductDocumentInDB(IDMixin, TimestampsMixin, table=True):
    """Документ на товар в БД"""

    __tablename__: ClassVar[str | Callable[..., str]] = "document"
    __table_args__: dict[str, str | None] = {"schema": metadata.schema}
    key: str = Field(description="Ключ на документ в хранилище", sa_column=Column(String, nullable=False))
    name: str = Field(description="Название документа", sa_column=Column(String, nullable=False))
    extension: str = Field(description="Расширение документа", sa_column=Column(String, nullable=False))
    product_id: UUID = Field(
        description="ID товара", sa_column=Column(Uuid, ForeignKey(f"{metadata.schema}.product.id", ondelete="CASCADE"))
    )
    product: "ProductInDB" = Relationship(
        back_populates="documents",
        sa_relationship=RelationshipProperty(back_populates="documents", uselist=False, single_parent=True),
    )


class ProductPackInDB(IDMixin, TimestampsMixin, table=True):
    """Характеристики упаковки товара в БД"""

    __tablename__: ClassVar[str | Callable[..., str]] = "pack"
    __table_args__: tuple = (
        UniqueConstraint("product_id"),
        {"schema": metadata.schema},
    )
    length: int = Field(description="Длина упаковки, мм", sa_column=Column(Integer, nullable=False))
    width: int = Field(description="Ширина упаковки, мм", sa_column=Column(Integer, nullable=False))
    height: int = Field(description="Высота упаковки, мм", sa_column=Column(Integer, nullable=False))

    weight_packed: int = Field(
        description="Вес товара в упаковке (брутто), г", sa_column=Column(Integer, nullable=False)
    )
    product_id: UUID = Field(
        description="ID товара",
        sa_column=Column(Uuid, ForeignKey(f"{metadata.schema}.product.id", ondelete="CASCADE"), nullable=False),
    )
    product: "ProductInDB" = Relationship(
        back_populates="pack",
        sa_relationship=RelationshipProperty(back_populates="pack", uselist=False, single_parent=True),
    )
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ProductPriceInDB(IDMixin, TimestampsMixin, table=True):
    """Цена товара в БД"""

    __tablename__: ClassVar[str | Callable[..., str]] = "price"
    __table_args__: tuple = (
        UniqueConstraint("product_id"),
        {"schema": metadata.schema},
    )
    product_id: UUID = Field(
        description="ID товара",
        sa_column=Column(Uuid, ForeignKey(f"{metadata.schema}.product.id", ondelete="CASCADE"), nullable=False),
    )
    product: "ProductInDB" = Relationship(
        back_populates="price",
        sa_relationship=RelationshipProperty(back_populates="price", uselist=False, single_parent=True),
    )
    price_with_discount: float = Field(
        description="Цена товара (c учётом скидки, конечная цена), руб.", sa_column=Column(Float, nullable=False)
    )
    price_without_discount: float | None = Field(
        description="Цена товара до скидки, руб.", default=None, sa_column=Column(Float, nullable=True)
    )
    vat: ValueAddedTax = Field(
        description="Размер НДС",
        sa_column=Column(
            psEnum(
                ValueAddedTax,
                schema=metadata.schema,
            ),
            nullable=False,
        ),
    )
    model_config = ConfigDict(arbitrary_types_allowed=True)


class ProductManuallyFilledSpecificationInDB(IDMixin, TimestampsMixin, table=True):
    """Характеристики товара, заполняемые вручную, в БД"""

    __tablename__: ClassVar[str | Callable[..., str]] = "manually_filled_specification"
    __table_args__: tuple = (
        UniqueConstraint("product_id"),
        {"schema": metadata.schema},
    )
    type: str = Field(
        description="Тип товара",
        sa_column=Column(String, nullable=False),
    )
    custom_properties: dict[str, Any] | None = Field(
        default=None,
        description="Характеристики товара, добавляемые продавцом самостоятельно",
        sa_column=Column(JSON, nullable=True, default=None),
    )
    description: str | None = Field(
        default=None, description="Описание товаре", sa_column=Column(Text, nullable=True, default=None)
    )
    weight: int | None = Field(
        description="Вес товара (нетто), г", sa_column=Column(Integer, nullable=True, default=None)
    )
    length: int | None = Field(
        description="Длина товара в собранном виде, мм", sa_column=Column(Integer, nullable=True, default=None)
    )
    width: int | None = Field(
        description="Ширина товара в собранном виде, мм", sa_column=Column(Integer, nullable=True, default=None)
    )
    height: int | None = Field(
        description="Высота товара в собранном виде, мм", sa_column=Column(Integer, nullable=True, default=None)
    )
    product_id: UUID = Field(
        description="ID товара",
        sa_column=Column(
            Uuid,
            ForeignKey(f"{metadata.schema}.product.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    product: "ProductInDB" = Relationship(
        back_populates="price",
        sa_relationship=RelationshipProperty(
            uselist=False,
            back_populates="manually_filled_specification",
            single_parent=True,
        ),
    )


class ProductColorInDB(IDMixin, table=True):
    """Цвет продукта в БД"""

    __tablename__: ClassVar[str | Callable[..., str]] = "color"
    __table_args__: dict[str, str | None] = {"schema": metadata.schema}
    name: str = Field(
        description="Название цвета на русском языке",
        sa_column=Column(String, nullable=False),
    )
    html_code: str = Field(
        description="HTML-код цвета",
        sa_column=Column(String, nullable=False),
    )
    products: list["ProductInDB"] = Relationship(
        back_populates="color",
        sa_relationship=RelationshipProperty(
            back_populates="color",
            uselist=True,
            lazy="selectin",
        ),
    )


class ProductSizeInDB(IDMixin, table=True):
    """Размер продукта в БД"""

    __tablename__: ClassVar[str | Callable[..., str]] = "size"
    __table_args__: dict[str, str | None] = {"schema": metadata.schema}
    group_name: SizeGroup = Field(
        description="Название группы размеров на русском языке",
        sa_column=Column(
            psEnum(
                SizeGroup,
                schema=metadata.schema,
            ),
            nullable=False,
        ),
    )
    value: str = Field(
        description="Размер",
        sa_column=Column(String, nullable=False),
    )
    products: list["ProductInDB"] = Relationship(
        back_populates="size",
        sa_relationship=RelationshipProperty(
            back_populates="size",
            uselist=True,
            lazy="selectin",
        ),
    )


class ProductBrandInDB(IDMixin, table=True):
    """Бренд продукта в БД."""

    __tablename__: ClassVar[str | Callable[..., str]] = "brand"
    __table_args__: dict[str, str | None] = {"schema": metadata.schema}
    name: str = Field(
        description="Название бренда",
        sa_column=Column(String, nullable=False),
    )
    products: list["ProductInDB"] = Relationship(
        back_populates="brand",
        sa_relationship=RelationshipProperty(
            back_populates="brand",
            uselist=True,
            lazy="selectin",
        ),
    )


class ProductMessageInDB(IDMixin, TimestampsMixin, table=True):
    """Cообщение о модерации продукта"""

    __tablename__: ClassVar[str | Callable[..., str]] = "message"
    __table_args__: dict[str, str | None] = {"schema": metadata.schema}
    product_id: UUID = Field(
        description="""
        ID продукта
        """,
        sa_column=Column(
            Uuid,
            ForeignKey(f"{metadata.schema}.product.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )
    message: str = Field(
        description="""
        Сообщение
        """,
        sa_column=Column(Text, nullable=False, default=None),
    )
    is_active: bool = Field(
        description="""
        Статус сообщения
        """,
        sa_column=Column(Boolean, default=True, nullable=False),
    )
    product: "ProductInDB" = Relationship(
        back_populates="messages",
        sa_relationship=RelationshipProperty(back_populates="messages", uselist=False, single_parent=True),
    )
