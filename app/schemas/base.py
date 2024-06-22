from humps import camelize
from pydantic import BaseModel, ConfigDict, Field


class PaginationBase(BaseModel):
    page: int | None = Field(
        default=None,
        description="""
        Номер страницы
        """,
    )
    size: int | None = Field(
        default=None,
        description="""
        Товаров на странице
        """,
    )
    total_count: int | None = Field(
        default=0,
        description="""
        Общее количество товаров
        """,
    )
    total_pages: int | None = Field(
        default=1,
        description="""
        Общее количество страниц
        """,
    )
    model_config = ConfigDict(
        title="Pagination Base",
        alias_generator=camelize,
        populate_by_name=True,
        json_schema_extra={"examples": [{"page": 1, "size": 1, "totalCount": 1, "totalPages": 1}]},
    )
