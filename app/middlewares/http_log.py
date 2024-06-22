from logging import debug

from fastapi.requests import Request
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send


class HTTPLogMiddleware:
    def __init__(
        self,
        app: ASGIApp,
    ) -> None:
        self.app: ASGIApp = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] == "http":
            request: Request = Request(
                scope=scope,
                receive=receive,
            )
            headers: Headers = Headers(
                scope=scope,
            )

            debug(f"{request.method} {request.url}")

            debug("Params:")
            for name, value in request.path_params.items():
                debug(f"\t{name}: {value}")

            debug("Headers:")
            for name, value in headers.items():
                debug(f"\t{name}: {value}")

        return await self.app(scope, receive, send)
