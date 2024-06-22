from typing import Any

from app.schemas import exceptions

responses: dict[str | int, dict[str, Any]] = {
    "400": {
        "model": exceptions.BadRequest,
    },
    "401": {
        "model": exceptions.Unauthorized,
    },
    "403": {
        "model": exceptions.Forbidden,
    },
    "404": {
        "model": exceptions.NotFound,
    },
    "405": {
        "model": exceptions.MethodNotAllowed,
    },
    "406": {
        "model": exceptions.NotAcceptable,
    },
    "415": {
        "model": exceptions.UnsupportedMediaType,
    },
    "422": {
        "model": exceptions.UnprocessableEntity,
    },
    "429": {
        "model": exceptions.TooManyRequests,
    },
    "500": {
        "model": exceptions.InternalServerError,
    },
    "501": {
        "model": exceptions.NotImplemented,
    },
}
