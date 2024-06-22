from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from msgpack_asgi import MessagePackMiddleware
from starlette.middleware import Middleware

from app.middlewares.http_log import HTTPLogMiddleware

middleware = [
    Middleware(
        HTTPLogMiddleware,
    ),
    Middleware(
        CORSMiddleware,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_origins=["*"],
        allow_credentials=True,
    ),
    Middleware(
        GZipMiddleware,
        minimum_size=50,
    ),
    Middleware(
        MessagePackMiddleware,
    ),
]
