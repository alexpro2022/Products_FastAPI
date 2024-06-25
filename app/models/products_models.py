from typing import Callable, ClassVar
from uuid import UUID

from pydantic import ConfigDict
from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, String, Uuid
from sqlalchemy.dialects.postgresql import ENUM as psEnum
from sqlalchemy.orm import RelationshipProperty
from sqlmodel import Field, Relationship, UniqueConstraint

from app.db import metadata
from app.models.base import IDMixin, TimestampsMixin
from app.models.fields_extensions_models import (
    GenderType,
    ProductBrandInDB,
    ProductColorInDB,
    ProductDocumentInDB,
    ProductImageInDB,
    ProductManuallyFilledSpecificationInDB,
    ProductMessageInDB,
    ProductPackInDB,
    ProductPriceInDB,
    ProductSizeInDB,
    ProductStatus,
)


class ProductCategoryInDB(IDMixin, TimestampsMixin, table=True):
    """Категория товара в БД"""

    __tablename__: ClassVar[str | Callable[..., str]] = "category"
    __table_args__: dict[str, str | None] = {"schema": metadata.schema}
    name: str = Field(
        description="Наименование категории товара", sa_column=Column(String(255), nullable=False, index=True)
    )
    name_slug: str = Field(
        description="URL категории товара", sa_column=Column(String(255), nullable=False, unique=True, index=True)
    )
    subcategories: list["ProductSubCategoryInDB"] = Relationship(
        back_populates="category",
        sa_relationship=RelationshipProperty(
            back_populates="category",
            uselist=True,
            lazy="selectin",
            cascade="all, delete",
        ),
    )


class ProductSubCategoryInDB(IDMixin, TimestampsMixin, table=True):
    """Подкатегория товара в БД"""

    __tablename__: ClassVar[str | Callable[..., str]] = "subcategory"
    __table_args__: tuple = (
        UniqueConstraint("category_id", "name_slug"),
        {"schema": metadata.schema},
    )
    name: str = Field(
        description="Наименование подкатегории товара", sa_column=Column(String(255), nullable=False, index=True)
    )
    name_slug: str = Field(
        description="URL подкатегории товара",
        sa_column=Column(
            String(255),
            nullable=False,
            index=True,
            unique=False,
        ),
    )
    category_id: UUID = Field(
        sa_column=Column(
            Uuid,
            ForeignKey(f"{metadata.schema}.category.id"),
            nullable=True,
        )
    )
    category: ProductCategoryInDB = Relationship(
        back_populates="subcategories",
        sa_relationship=RelationshipProperty(lazy="joined", uselist=False, back_populates="subcategories"),
    )
    products: list["ProductInDB"] = Relationship(
        back_populates="subcategory",
        sa_relationship=RelationshipProperty(
            "ProductInDB", uselist=True, lazy="selectin", back_populates="subcategory"
        ),
    )


class ProductInDB(IDMixin, TimestampsMixin, table=True):
    """Товар в БД"""

    __tablename__: ClassVar[str | Callable[..., str]] = "product"
    __table_args__: tuple = (
        UniqueConstraint("id", "external_id"),
        {"schema": metadata.schema},
    )
    seller_id: UUID = Field(
        description="ID продавца (получать в сервисе sellers при регистрации компании)",
        sa_column=Column(Uuid(as_uuid=True), nullable=False, index=True),
    )
    external_id: str | None = Field(
        description="ID товара в учётной системе продавца",
        sa_column=Column(
            String(255),
            default=None,
            nullable=True,
        ),
    )
    is_active: bool = Field(description="Активность товара", sa_column=Column(Boolean, default=False, nullable=False))
    status: ProductStatus = Field(
        default=ProductStatus.new,
        description="Статус товара",
        sa_column=Column(
            psEnum(
                ProductStatus,
                name="product_status_enum",
                schema=metadata.schema,
            ),
            nullable=False,
        ),
    )
    name: str = Field(description="Наименование товара", sa_column=Column(String(128), nullable=False, index=True))
    name_slug: str = Field(
        description="URL товара",
        sa_column=Column(String(255), unique=True, index=True, nullable=False),
    )
    country_of_manufacture: str = Field(
        description="Страна производства товара",
        sa_column=Column(
            String(255),
            nullable=False,
        ),
    )
    vendor_code: str = Field(
        description="Артикул товара",
        sa_column=Column(
            String(255),
            nullable=False,
        ),
    )
    barcode: int = Field(description="Штрихкод товара", sa_column=Column(BigInteger, nullable=False))
    pack: ProductPackInDB = Relationship(
        back_populates="product",
        sa_relationship=RelationshipProperty(uselist=False, lazy="selectin", back_populates="product"),
    )
    subcategory_id: UUID = Field(
        description="""
        ID подкатегории товара
        """,
        sa_column=Column(
            Uuid(as_uuid=True), ForeignKey(f"{metadata.schema}.subcategory.id", ondelete="SET NULL"), nullable=True
        ),
    )
    subcategory: ProductSubCategoryInDB = Relationship(
        back_populates="products",
        sa_relationship=RelationshipProperty(
            lazy="joined",
            uselist=False,
            back_populates="products",
        ),
    )
    images: list[ProductImageInDB] = Relationship(
        back_populates="product",
        sa_relationship=RelationshipProperty(
            uselist=True,
            lazy="selectin",
            back_populates="product",
            cascade="all, delete",
        ),
    )
    manually_filled_specification: ProductManuallyFilledSpecificationInDB = Relationship(
        back_populates="product",
        sa_relationship=RelationshipProperty(
            uselist=False,
            back_populates="product",
            cascade="all, delete",
            lazy="selectin",
        ),
    )
    gender: GenderType | None = Field(
        default=None,
        description="Пол (только для категории Одежда и обувь)",
        sa_column=Column(
            psEnum(
                GenderType,
                schema=metadata.schema,
            ),
            nullable=True,
        ),
    )
    color: ProductColorInDB = Relationship(
        back_populates="products",
        sa_relationship=RelationshipProperty(lazy="joined", uselist=False, back_populates="products"),
    )
    color_id: UUID | None = Field(
        description="ID цвета товара",
        sa_column=Column(
            Uuid(as_uuid=True), ForeignKey(f"{metadata.schema}.color.id", ondelete="SET NULL"), nullable=True
        ),
    )
    size: ProductSizeInDB = Relationship(
        back_populates="products",
        sa_relationship=RelationshipProperty(lazy="joined", uselist=False, back_populates="products"),
    )
    size_id: UUID | None = Field(
        description="ID размера товара (только для категории Одежда и обувь)",
        sa_column=Column(
            Uuid(as_uuid=True), ForeignKey(f"{metadata.schema}.size.id", ondelete="SET NULL"), nullable=True
        ),
    )
    brand: ProductBrandInDB = Relationship(
        back_populates="products",
        sa_relationship=RelationshipProperty(lazy="joined", uselist=False, back_populates="products"),
    )
    brand_id: UUID | None = Field(
        description="ID бренда товара",
        sa_column=Column(
            Uuid(as_uuid=True), ForeignKey(f"{metadata.schema}.brand.id", ondelete="SET NULL"), nullable=True
        ),
    )
    price: ProductPriceInDB = Relationship(
        back_populates="product",
        sa_relationship=RelationshipProperty(
            uselist=False, back_populates="product", cascade="all, delete", lazy="selectin"
        ),
    )
    documents: list[ProductDocumentInDB] = Relationship(
        back_populates="product",
        sa_relationship=RelationshipProperty(
            uselist=True,
            lazy="selectin",
            back_populates="product",
            cascade="all, delete",
        ),
    )
    messages: list[ProductMessageInDB] = Relationship(
        back_populates="product",
        sa_relationship=RelationshipProperty(uselist=True, back_populates="product", lazy="selectin"),
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)
