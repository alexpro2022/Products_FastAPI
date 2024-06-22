import sys
from asyncio import run
from pathlib import Path

from slugify.slugify import slugify

sys.path.append(str(Path(__file__).parent.parent))
from data.brands import brands  # noqa
from data.categories_tree import categories_tree  # noqa
from data.clothes_sizes import clothes_sizes  # noqa
from data.colors import colors  # noqa

from app.db import async_session  # noqa
from app.models.fields_extensions_models import ProductBrandInDB, ProductColorInDB, ProductSizeInDB  # noqa
from app.models.products_models import ProductCategoryInDB  # noqa
from app.models.products_models import ProductSubCategoryInDB  # noqa


async def populate_db():
    async with async_session() as session:
        for category in categories_tree:
            category_instance = ProductCategoryInDB(name=category, name_slug=slugify(str(category)))
            session.add(category_instance)
            [
                category_instance.subcategories.append(
                    ProductSubCategoryInDB(name=subcategory, name_slug=slugify(str(subcategory)))
                )
                for subcategory in categories_tree[category]
            ]

        [session.add(ProductColorInDB(name=color["name"], html_code=color["html_code"])) for color in colors]

        [
            [session.add(ProductSizeInDB(group_name=group, value=size)) for size in sizes]
            for group, sizes in clothes_sizes.items()
        ]

        [
            [
                session.add(
                    ProductBrandInDB(
                        name=brand,
                    )
                )
                for brand in brands
            ]
            for category, brands in brands.items()
        ]

        await session.commit()


if __name__ == "__main__":
    run(
        main=populate_db(),
    )
