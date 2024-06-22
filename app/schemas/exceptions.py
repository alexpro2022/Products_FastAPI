from pydantic import ConfigDict
from pydantic.fields import Field
from pydantic.main import BaseModel


class BadRequest(BaseModel):
    status_code: int = Field(
        default=400,
        description="Response status code",
    )
    detail: str = Field(
        default="Bad Request",
        description="Response Detail",
    )
    model_config = ConfigDict()


class Unauthorized(BaseModel):
    status_code: int = Field(
        default=401,
        description="Response status code",
    )
    detail: str = Field(
        default="Unauthorized",
        description="Response Detail",
    )
    model_config = ConfigDict()


class Forbidden(BaseModel):
    status_code: int = Field(
        default=403,
        description="Response status code",
    )
    detail: str = Field(
        default="Forbidden",
        description="Response Detail",
    )
    model_config = ConfigDict()


class NotFound(BaseModel):
    status_code: int = Field(
        default=404,
        description="Response status code",
    )
    detail: str = Field(
        default="Not Found",
        description="Response Detail",
    )
    model_config = ConfigDict()


class MethodNotAllowed(BaseModel):
    status_code: int = Field(
        default=404,
        description="Response status code",
    )
    detail: str = Field(
        default="Method Not Allowed",
        description="Response Detail",
    )
    model_config = ConfigDict()


class NotAcceptable(BaseModel):
    status_code: int = Field(
        default=406,
        description="Response status code",
    )
    detail: str = Field(
        default="Not Acceptable",
        description="Response Detail",
    )
    model_config = ConfigDict()


class UnsupportedMediaType(BaseModel):
    status_code: int = Field(
        default=415,
        description="Response status code",
    )
    detail: str = Field(
        default="Unsupported Media Type",
        description="Response Detail",
    )
    model_config = ConfigDict()


class UnprocessableEntity(BaseModel):
    status_code: int = Field(
        default=422,
        description="Response status code",
    )
    detail: str = Field(
        default="Unprocessable Entity",
        description="Response Detail",
    )
    model_config = ConfigDict()


class TooManyRequests(BaseModel):
    status_code: int = Field(
        default=415,
        description="Response status code",
    )
    detail: str = Field(
        default="Too Many Requests",
        description="Response Detail",
    )
    model_config = ConfigDict()


class InternalServerError(BaseModel):
    status_code: int = Field(
        default=500,
        description="Response status code",
    )
    detail: str = Field(
        default="Internal Server Error",
        description="Response Detail",
    )
    model_config = ConfigDict()


class NotImplemented(BaseModel):
    status_code: int = Field(
        default=501,
        description="Response status code",
    )
    detail: str = Field(
        default="Not Implemented",
        description="Response Detail",
    )
    model_config = ConfigDict()


class UnknownError(BaseModel):
    status_code: int = Field(
        default=520,
        description="Response status code",
    )
    detail: str = Field(
        default="Unknown Error",
        description="Response Detail",
    )
    model_config = ConfigDict()
