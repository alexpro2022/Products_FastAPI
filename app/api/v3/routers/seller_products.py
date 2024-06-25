from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request, Response, status

from app.core.config import settings
from app.middlewares.auth import SellerCheck
from app.middlewares.request_info import set_request_info
from app.models.fields_extensions_models import ProductStatusForChange
from app.models.products_models import (
    ProductBrandInDB,
    ProductCategoryInDB,
    ProductColorInDB,
    ProductInDB,
    ProductPriceInDB,
    ProductSizeInDB,
)
from app.schemas.categories_schemas import ProductCategory
from app.schemas.fields_extensions_schemas import ProductBrand, ProductColor, ProductPrice, ProductSize
from app.schemas.products_schemas import (
    ProductCreate,
    ProductPagination,
    ProductRead,
    ProductReadNotСonfidential,
    ProductUpdate,
    ReadProductName,
)
from app.services.seller_products import Service, get_service

router = APIRouter(
    prefix=f"/{settings.app_settings.service_name}/api/v3",
    dependencies=[
        Depends(
            dependency=set_request_info,
        )
    ],
)

setattr(router, "version", "v3")
setattr(router, "service_name", "products")

seller_check = SellerCheck()


@router.post(
    path="/products/create",
    status_code=status.HTTP_201_CREATED,
    name="product:create",
    tags=["Товар продавца"],
    summary="Товар продавца: создать",
    operation_id="product:create",
    response_model=ProductRead,
    dependencies=[
        Depends(seller_check),
    ],
)
async def create_product(
    request: Request, product: ProductCreate, service: Service = Depends(dependency=get_service)
) -> ProductInDB:
    return await service.create_product(
        seller_id=getattr(request, "seller_id"),
        product=product,
    )


@router.post(
    path="/products/get-by-ids",
    status_code=status.HTTP_200_OK,
    name="product:get_by_ids",
    tags=["Товар продавца"],
    summary="Товар продавца: получить информацию о товарах по их id",
    operation_id="product:get_by_ids",
    response_model=list[ProductReadNotСonfidential],
)
async def get_products_by_ids(
    product_ids: list[UUID],
    service: Service = Depends(dependency=get_service),
) -> list[ProductInDB]:
    return await service.get_products_by_ids(
        product_ids=product_ids,
    )


@router.get(
    path="/products/get-name/{product_id}",
    status_code=status.HTTP_200_OK,
    name="product:get_name_by_id",
    tags=["Товар продавца"],
    summary="Товар продавца: получить наименование по айди",
    operation_id="product:get_name_by_id",
    response_model=ReadProductName,
    dependencies=[
        Depends(seller_check),
    ],
)
async def get_name_by_id(
    product_id: UUID,
    request: Request,
    background_tasks: BackgroundTasks,
    service: Service = Depends(dependency=get_service),
) -> ProductInDB:
    return await service.get_name_by_id(
        product_id=product_id, request_info=getattr(request, "request_info"), background_tasks=background_tasks
    )


@router.get(
    path="/products/get-by-slug/{product_slug}",
    status_code=status.HTTP_200_OK,
    name="product:get_product_by_name_slug",
    tags=["Товар продавца"],
    summary="Товар продавца: получить один по slug",
    operation_id="product:get_product_by_name_slug",
    response_model=ProductReadNotСonfidential,
)
async def get_product_by_name_slug(
    product_slug: str, request: Request, service: Service = Depends(dependency=get_service)
) -> ProductInDB:
    return await service.get_one(product_slug=product_slug)


@router.get(
    path="/products/get-all",
    status_code=status.HTTP_200_OK,
    name="product:get_all",
    tags=["Товар продавца"],
    summary="Товар продавца: получить все",
    operation_id="product:get_all",
    response_model=ProductPagination,
    dependencies=[
        Depends(seller_check),
    ],
)
async def get_all(
    request: Request,
    page: int = Query(
        default=1,
        ge=1,
    ),
    size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    service: Service = Depends(dependency=get_service),
) -> ProductPagination:
    return await service.get_all(seller_id=getattr(request, "seller_id"), page=page, size=size)


# @router.delete(
#     path="/products/delete/{product_id}",
#     status_code=status.HTTP_204_NO_CONTENT,
#     name="product:delete",
#     tags=["Товар продавца"],
#     summary="Товар продавца: удалить",
#     operation_id="product:delete",
#     dependencies=[
#         Depends(seller_check),
#     ],
# )
# async def delete(
#         product_id: UUID,
#         request: Request,
#         service: Service = Depends(
#             dependency=get_service
#         )
# ) -> Response:
#     # FIXME: Не работает. Необходимо переделать реализацию.
#     return await service.delete(
#         seller_id=getattr(request, 'seller_id'),
#         product_id=product_id,
#     )


# @router.delete(
#     path='/products/delete-all',
#     status_code=status.HTTP_204_NO_CONTENT,
#     name="product:delete all",
#     tags=["Товар продавца"],
#     summary="Товар продавца: удалить все",
#     operation_id="product:delete all",
#     dependencies=[
#         Depends(seller_check),
#     ],
# )
# async def delete_all(
#         request: Request,
#         service: Service = Depends(
#             dependency=get_service
#         )
# ) -> Response:
#     # FIXME: Не работает. Необходимо переделать реализацию.
#     return await service.delete_all(
#         seller_id=getattr(request, 'seller_id'),
#     )


@router.patch(
    path="/products/update/{product_id}",
    status_code=status.HTTP_200_OK,
    response_model=ProductRead,
    name="product:update",
    tags=["Товар продавца"],
    summary="Товар продавца: обновить",
    operation_id="product:update",
    dependencies=[
        Depends(seller_check),
    ],
)
async def update(
    request: Request, product_id: UUID, product: ProductUpdate, service: Service = Depends(dependency=get_service)
) -> ProductInDB:
    return await service.edit(
        seller_id=getattr(request, "seller_id"),
        product_id=product_id,
        product=product,
    )


@router.get(
    path="/products/get-document/{document_id}",
    status_code=status.HTTP_200_OK,
    name="product:get_document",
    tags=["Товар продавца"],
    summary="Товар продавца: получить документ",
    operation_id="product:get_document",
    dependencies=[
        Depends(seller_check),
    ],
)
async def get_document(
    document_id: UUID,
    request: Request,
    service: Service = Depends(dependency=get_service),
) -> Response:
    return await service.get_document(
        document_id=document_id,
        seller_id=getattr(request, "seller_id"),
    )


@router.get(
    path="/sizes",
    status_code=status.HTTP_200_OK,
    name="size:get_all_sizes",
    tags=["Размер товара"],
    summary="Размер товара: получить все",
    operation_id="size:get_all_sizes",
    response_model=list[ProductSize],
)
async def get_all_sizes(
    request: Request,
    service: Service = Depends(dependency=get_service),
) -> dict[str, Any]:
    return await service.get_all_sizes()


@router.get(
    path="/colors",
    status_code=status.HTTP_200_OK,
    name="color:get_all_colors",
    tags=["Цвет товара"],
    summary="Цвет товара: получить все",
    operation_id="color:get_all_colors",
    response_model=list[ProductColor],
)
async def get_all_colors(
    request: Request,
    service: Service = Depends(dependency=get_service),
) -> dict[str, Any]:
    return await service.get_all_colors()


@router.get(
    path="/brands",
    status_code=status.HTTP_200_OK,
    name="brand:get_all_brands",
    tags=["Бренд товара"],
    summary="Бренд товара: получить все",
    operation_id="brand:get_all_brands",
    response_model=list[ProductBrand],
)
async def get_all_brands(
    request: Request,
    service: Service = Depends(dependency=get_service),
) -> dict[str, Any]:
    return await service.get_all_brands()


@router.get(
    path="/categories",
    status_code=status.HTTP_200_OK,
    name="category:get_all_categories_and_subcategories",
    tags=["Категория товара с подкатегориями"],
    summary="Категория товара с подкатегориями: получить все",
    operation_id="category:get_all_categories_and_subcategories",
    response_model=list[ProductCategory],
)
async def get_all_categories_and_subcategories(
    request: Request, service: Service = Depends(dependency=get_service)
) -> dict[str, Any]:
    return await service.get_all_categories_and_subcategories()


@router.post(
    path="/products/get-prices-by-ids",
    status_code=status.HTTP_200_OK,
    name="product:get_products_prices",
    tags=["Товар продавца"],
    summary="Товар продавца: получить цены товаров по их id",
    operation_id="product:get_products_prices",
    response_model=list[ProductPrice],
)
async def get_products_prices(
    product_ids: list[UUID],
    service: Service = Depends(dependency=get_service),
) -> list[ProductPriceInDB]:
    return await service.get_products_prices(
        product_ids=product_ids,
    )


@router.patch(
    path="/products/change-status/{product_id}",
    status_code=status.HTTP_200_OK,
    name="product:change_status",
    tags=["Товар продавца"],
    summary="Товар продавца: изменить статус",
    operation_id="product:change_status",
    dependencies=[
        Depends(seller_check),
    ],
)
async def change_product_status(
    product_id: UUID,
    product_status: ProductStatusForChange,
    request: Request,
    service: Service = Depends(dependency=get_service),
):
    return await service.change_product_status(
        seller_id=getattr(request, "seller_id"),
        user_token=getattr(request, "user_token"),
        product_id=product_id,
        product_status=product_status,
    )
