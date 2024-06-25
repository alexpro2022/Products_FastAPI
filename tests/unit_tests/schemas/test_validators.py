from typing import TypeAlias

import pytest
from fastapi.exceptions import HTTPException

from app.schemas import fields_extensions_schemas as fes
from app.schemas.castom_types import DocumentBase64File, ImageBase64File
from app.schemas.products_schemas import ProductCreate, ProductUpdate
from app.services.seller_products import Service
from tests import utils as d
from tests.mocks import SELLER_ID, UUID_ID

FileType: TypeAlias = DocumentBase64File | ImageBase64File

field_validator_parametrize = pytest.mark.parametrize(
    "klass",
    (
        fes.ProductManuallyFilledSpecificationUpdate,
        fes.ProductPackUpdate,
        fes.ProductPriceUpdate,
        ProductUpdate,
    ),
)
model_validator_parametrize = pytest.mark.parametrize(
    "klass, err_msg, required_attrs",
    (
        (fes.ProductDocumentUpdate, "the document and id cannot be missing at the same time", {}),
        (fes.ProductImageUpdate, "the image and id cannot be missing at the same time", {"order_num": 1}),
    ),
)


@field_validator_parametrize
def test_field_validator_raises_exc(klass):
    with pytest.raises(ValueError, match="The field cannot be null."):
        klass.validation_for_null(None)


@field_validator_parametrize
@pytest.mark.parametrize("valid_value", (123, 123.33, "123", [], {}))
def test_field_validator_returns_valid_value(klass, valid_value):
    assert klass.validation_for_null(valid_value) == valid_value


@model_validator_parametrize
def test_model_validator_raises_exc(klass, err_msg, required_attrs):
    with pytest.raises(ValueError, match=err_msg):
        klass(**required_attrs)


@model_validator_parametrize
def test_model_validator_with_valid_input(klass, err_msg, required_attrs):
    attr_name = "document" if klass is fes.ProductDocumentUpdate else "image"
    optional_attrs = {"id": UUID_ID, attr_name: None}
    inst = klass(**required_attrs, **optional_attrs)
    assert isinstance(inst, klass)


@pytest.mark.parametrize(
    "klass, patterns",
    (
        (DocumentBase64File, ("image/jpeg", "application/pdf")),
        (ImageBase64File, ("image/jpeg", "image/png")),
    ),
)
def test_validate_returns_crated_obj(klass: FileType, patterns: str) -> None:
    for pattern in patterns:
        mime, ext = pattern.split("/")
        value = d.get_content(mime, ext)
        result: FileType = klass.validate(value, "handler")
        assert isinstance(result, klass)
        assert isinstance(result.file, bytes)
        assert result.content_type == pattern
        assert result.file_format == ext


@pytest.mark.parametrize("klass", (DocumentBase64File, ImageBase64File))
@pytest.mark.parametrize(
    "invalid_value, err_msg",
    (
        (123, "the data must be of string type"),
        ("application/jpeg", "incorrect meta information about the file"),
    ),
)
def test_validate_raises_exc(klass, invalid_value, err_msg):
    with pytest.raises(ValueError, match=err_msg):
        klass.validate(invalid_value, "handler")


async def test_order_num_validator(get_service_dependencies, get_product_create_data) -> None:
    get_product_create_data["images"][0]["order_num"] = 1
    with pytest.raises(HTTPException, match="incorrect image order"):
        await Service(*get_service_dependencies).create_product(SELLER_ID, ProductCreate(**get_product_create_data))
