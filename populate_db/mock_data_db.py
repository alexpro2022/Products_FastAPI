import sys
from asyncio import run
from pathlib import Path

from faker import Faker
from slugify.slugify import slugify
from sqlalchemy import select

from app.models.products_models import (
    ProductBrandInDB,
    ProductInDB,
    ProductManuallyFilledSpecificationInDB,
    ProductPackInDB,
    ProductSubCategoryInDB,
)

sys.path.append(str(Path(__file__).parent.parent))
from app.db import async_session  # noqa
from app.models.fields_extensions_models import ProductPriceInDB  # noqa
from app.models.products_models import ProductColorInDB  # noqa


async def test_data_db():
    """Создаёт тестовые данные."""
    fake = Faker("ru-RU")
    async with async_session() as session:
        subcategories = await session.execute(statement=select(ProductSubCategoryInDB))
        colors = await session.execute(statement=select(ProductColorInDB))
        brands = await session.execute(statement=select(ProductBrandInDB))
        subcategories = subcategories.scalars().all()
        colors = colors.scalars().all()
        brands = brands.scalars().all()
        for _ in range(150):
            product = fake.unique.text(max_nb_chars=50)
            session.add(
                ProductInDB(
                    seller_id=fake.uuid4(),
                    external_id=fake.uuid4(),
                    is_active=fake.boolean(),
                    subcategory_id=fake.random_element(subcategories).id,
                    color_id=fake.random_element(colors).id,
                    brand_id=fake.random_element((None, fake.random_element(brands).id)),
                    name=product,
                    name_slug=slugify(product),
                    country_of_manufacture=fake.country(),
                    vendor_code=str(fake.unique.random_int(min=1)),
                    barcode=fake.unique.random_int(min=1),
                )
            )
        await session.commit()
        products = await session.execute(statement=select(ProductInDB))
        for product in products.scalars().all():
            price = float(fake.random_int(min=1))
            session.add(
                ProductPriceInDB(
                    product_id=product.id,
                    price_with_discount=price * 0.9,
                    price_without_discount=price,
                    vat="20%",
                )
            )
            session.add(
                ProductPackInDB(
                    length=fake.random_int(min=1),
                    width=fake.random_int(min=1),
                    height=fake.random_int(min=1),
                    weight_packed=fake.random_int(min=1),
                    product_id=product.id,
                )
            )
            session.add(
                ProductManuallyFilledSpecificationInDB(
                    type=fake.text(max_nb_chars=10),
                    product_id=product.id,
                )
            )
        await session.commit()


if __name__ == "__main__":
    run(
        main=test_data_db(),
    )
