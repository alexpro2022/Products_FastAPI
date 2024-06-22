import base64
import re
from dataclasses import dataclass
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core.core_schema import CoreSchema, no_info_wrap_validator_function, str_schema


@dataclass
class Base64File:
    """Класс файла в base64 строке."""

    file: bytes
    content_type: str
    file_format: str

    @classmethod
    def check_type_and_pattern_matching(cls, value: Any, pattern: str) -> None:
        """Проверка типа и совпадение строки по шаблону."""
        if not isinstance(value, str):
            raise ValueError("the data must be of string type")
        if not re.match(pattern, value):
            raise ValueError("incorrect meta information about the file")

    @classmethod
    def create_obj(cls, value: str) -> "Base64File":
        """Создаёт объект класса Base64File."""
        image_type, image_base64 = value.split(";base64,")
        content_type = image_type.replace("data:", "", 1)
        image_bytes = base64.b64decode(image_base64)
        file_format = content_type.split("/")[1]
        return cls(file=image_bytes, content_type=content_type, file_format=file_format)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return no_info_wrap_validator_function(
            function=cls.validate,
            schema=str_schema(),
        )


class ImageBase64File(Base64File):
    """Класс изображения в base64 строке."""

    @classmethod
    def validate(cls, value: Any, handler: GetCoreSchemaHandler) -> "ImageBase64File":
        """Валидирует данные."""
        pattern = r"data:(image/jpeg|image/png);base64,"
        cls.check_type_and_pattern_matching(value, pattern)
        return cls.create_obj(value)


class DocumentBase64File(Base64File):
    """Класс документа в base64 строке."""

    @classmethod
    def validate(cls, value: Any, handler: GetCoreSchemaHandler) -> "DocumentBase64File":
        """Валидирует данные."""
        pattern = r"data:(image/jpeg|application/pdf);base64,"
        cls.check_type_and_pattern_matching(value, pattern)
        return cls.create_obj(value)
