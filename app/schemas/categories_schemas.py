from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProductSubCategory(BaseModel):
    """Схема подкатегории."""

    id: UUID = Field(description="ID подкатегории")
    name: str = Field(
        description="Наименование подкатегории товара",
    )
    name_slug: str | None = Field(description="URL подкатегории товара")

    model_config = {
        "title": "Получение подкатегорий",
        "json_schema_extra": {"examples": [{"name": "computers", "category_id": str(uuid4())}]},
    }


class ProductCategory(BaseModel):
    """Схема категории с подкатегориями."""

    id: UUID = Field(description="ID категории")
    name: str = Field(description="Наименование категории товара")
    name_slug: str | None = Field(description="URL категории товара")
    subcategories: list[ProductSubCategory] = Field(description="Подкатегории")
    model_config = {
        "title": "Получение категорий с подкатегориями",
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Обувь",
                    "name_slug": "obuv",
                    "subcategories": (ProductSubCategory.model_config["json_schema_extra"]["examples"]),
                }
            ]
        },
    }
