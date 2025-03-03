"""Add brands and id.

Revision ID: cbca7bcad4db
Revises: 2697935b120e
Create Date: 2024-05-22 04:46:12.979963

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cbca7bcad4db"
down_revision: Union[str, None] = "2697935b120e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "brand",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="products",
    )
    op.create_index(op.f("ix_products_brand_id"), "brand", ["id"], unique=True, schema="products")
    op.add_column("product", sa.Column("brand_id", sa.Uuid(), nullable=True), schema="products")
    op.create_foreign_key(
        None,
        "product",
        "brand",
        ["brand_id"],
        ["id"],
        source_schema="products",
        referent_schema="products",
        ondelete="SET NULL",
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, "product", schema="products", type_="foreignkey")
    op.drop_column("product", "brand_id", schema="products")
    op.drop_index(op.f("ix_products_brand_id"), table_name="brand", schema="products")
    op.drop_table("brand", schema="products")
    # ### end Alembic commands ###
