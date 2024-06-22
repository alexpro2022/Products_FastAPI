"""Initial migration

Revision ID: 2697935b120e
Revises:
Create Date: 2024-05-08 23:11:22.599652

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlalchemy_utils
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2697935b120e"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "category",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_slug", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="products",
    )
    op.create_index(op.f("ix_products_category_id"), "category", ["id"], unique=True, schema="products")
    op.create_index(op.f("ix_products_category_name"), "category", ["name"], unique=False, schema="products")
    op.create_index(op.f("ix_products_category_name_slug"), "category", ["name_slug"], unique=True, schema="products")
    op.create_table(
        "color",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("html_code", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="products",
    )
    op.create_index(op.f("ix_products_color_id"), "color", ["id"], unique=True, schema="products")
    op.create_table(
        "request_info",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_agent", sa.String(), server_default=sa.text("NULL"), nullable=True),
        sa.Column("cookie", sa.String(), server_default=sa.text("NULL"), nullable=True),
        sa.Column("real_ip", sqlalchemy_utils.types.ip_address.IPAddressType(length=50), nullable=True),
        sa.Column("referer", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="products",
    )
    op.create_index(op.f("ix_products_request_info_id"), "request_info", ["id"], unique=True, schema="products")
    op.create_index(
        op.f("ix_products_request_info_real_ip"), "request_info", ["real_ip"], unique=False, schema="products"
    )
    op.create_table(
        "size",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column(
            "group_name", postgresql.ENUM("children", "adult", name="sizegroup", schema="products"), nullable=False
        ),
        sa.Column("value", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="products",
    )
    op.create_index(op.f("ix_products_size_id"), "size", ["id"], unique=True, schema="products")
    op.create_table(
        "subcategory",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_slug", sa.String(length=255), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["products.category.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category_id", "name_slug"),
        schema="products",
    )
    op.create_index(op.f("ix_products_subcategory_id"), "subcategory", ["id"], unique=True, schema="products")
    op.create_index(op.f("ix_products_subcategory_name"), "subcategory", ["name"], unique=False, schema="products")
    op.create_index(
        op.f("ix_products_subcategory_name_slug"), "subcategory", ["name_slug"], unique=False, schema="products"
    )
    op.create_table(
        "product",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("seller_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("name_slug", sa.String(length=255), nullable=False),
        sa.Column("country_of_manufacture", sa.String(length=255), nullable=False),
        sa.Column("vendor_code", sa.String(length=255), nullable=False),
        sa.Column("barcode", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("subcategory_id", sa.Uuid(), nullable=True),
        sa.Column("gender", postgresql.ENUM("male", "female", name="gendertype", schema="products"), nullable=True),
        sa.Column("color_id", sa.Uuid(), nullable=True),
        sa.Column("size_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["category_id"], ["products.category.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["color_id"], ["products.color.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["size_id"], ["products.size.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subcategory_id"], ["products.subcategory.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("id", "external_id"),
        schema="products",
    )
    op.create_index(op.f("ix_products_product_id"), "product", ["id"], unique=True, schema="products")
    op.create_index(op.f("ix_products_product_name"), "product", ["name"], unique=False, schema="products")
    op.create_index(op.f("ix_products_product_name_slug"), "product", ["name_slug"], unique=True, schema="products")
    op.create_index(op.f("ix_products_product_seller_id"), "product", ["seller_id"], unique=False, schema="products")
    op.create_table(
        "document",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["product_id"], ["products.product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="products",
    )
    op.create_index(op.f("ix_products_document_id"), "document", ["id"], unique=True, schema="products")
    op.create_table(
        "image",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("preview_url", sa.String(), nullable=False),
        sa.Column("mini_url", sa.String(), nullable=False),
        sa.Column("small_url", sa.String(), nullable=False),
        sa.Column("order_num", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        schema="products",
    )
    op.create_index(op.f("ix_products_image_id"), "image", ["id"], unique=True, schema="products")
    op.create_table(
        "manually_filled_specification",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("brandname", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("custom_properties", sa.JSON(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("weight", sa.Integer(), nullable=True),
        sa.Column("length", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
        schema="products",
    )
    op.create_index(
        op.f("ix_products_manually_filled_specification_brandname"),
        "manually_filled_specification",
        ["brandname"],
        unique=False,
        schema="products",
    )
    op.create_index(
        op.f("ix_products_manually_filled_specification_id"),
        "manually_filled_specification",
        ["id"],
        unique=True,
        schema="products",
    )
    op.create_table(
        "pack",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("length", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("weight_packed", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
        schema="products",
    )
    op.create_index(op.f("ix_products_pack_id"), "pack", ["id"], unique=True, schema="products")
    op.create_table(
        "price",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("product_id", sa.Uuid(), nullable=False),
        sa.Column("price_with_discount", sa.Float(), nullable=False),
        sa.Column("price_without_discount", sa.Float(), nullable=True),
        sa.Column(
            "vat",
            postgresql.ENUM("not_taxed", "null", "ten", "twenty", name="valueaddedtax", schema="products"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.product.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
        schema="products",
    )
    op.create_index(op.f("ix_products_price_id"), "price", ["id"], unique=True, schema="products")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_products_price_id"), table_name="price", schema="products")
    op.drop_table("price", schema="products")
    op.drop_index(op.f("ix_products_pack_id"), table_name="pack", schema="products")
    op.drop_table("pack", schema="products")
    op.drop_index(
        op.f("ix_products_manually_filled_specification_id"),
        table_name="manually_filled_specification",
        schema="products",
    )
    op.drop_index(
        op.f("ix_products_manually_filled_specification_brandname"),
        table_name="manually_filled_specification",
        schema="products",
    )
    op.drop_table("manually_filled_specification", schema="products")
    op.drop_index(op.f("ix_products_image_id"), table_name="image", schema="products")
    op.drop_table("image", schema="products")
    op.drop_index(op.f("ix_products_document_id"), table_name="document", schema="products")
    op.drop_table("document", schema="products")
    op.drop_index(op.f("ix_products_product_seller_id"), table_name="product", schema="products")
    op.drop_index(op.f("ix_products_product_name_slug"), table_name="product", schema="products")
    op.drop_index(op.f("ix_products_product_name"), table_name="product", schema="products")
    op.drop_index(op.f("ix_products_product_id"), table_name="product", schema="products")
    op.drop_table("product", schema="products")
    op.drop_index(op.f("ix_products_subcategory_name_slug"), table_name="subcategory", schema="products")
    op.drop_index(op.f("ix_products_subcategory_name"), table_name="subcategory", schema="products")
    op.drop_index(op.f("ix_products_subcategory_id"), table_name="subcategory", schema="products")
    op.drop_table("subcategory", schema="products")
    op.drop_index(op.f("ix_products_size_id"), table_name="size", schema="products")
    op.drop_table("size", schema="products")
    op.drop_index(op.f("ix_products_request_info_real_ip"), table_name="request_info", schema="products")
    op.drop_index(op.f("ix_products_request_info_id"), table_name="request_info", schema="products")
    op.drop_table("request_info", schema="products")
    op.drop_index(op.f("ix_products_color_id"), table_name="color", schema="products")
    op.drop_table("color", schema="products")
    op.drop_index(op.f("ix_products_category_name_slug"), table_name="category", schema="products")
    op.drop_index(op.f("ix_products_category_name"), table_name="category", schema="products")
    op.drop_index(op.f("ix_products_category_id"), table_name="category", schema="products")
    op.drop_table("category", schema="products")
    # ### end Alembic commands ###
