from http import HTTPStatus
from logging import config as logging_config
from typing import Any

from fastapi import Depends, FastAPI, status
from fastapi.exceptions import HTTPException
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uvicorn import run

from app.api.setup import setup_docs, setup_router
from app.api.v3.api import routers as v3_routers
from app.core.config import settings
from app.core.logger import get_logging_config
from app.db import close_connection, get_session, init_db
from app.middlewares import middleware
from app.mq import RabbitMQ, get_rabbitmq

IS_DEBUG: bool = settings.app_settings.is_debug or False
LOG_LEVEL: str = settings.app_settings.log_level or "INFO"

log_config: dict[str, Any] = get_logging_config(
    log_level=LOG_LEVEL,
)

logging_config.dictConfig(
    config=log_config,
)


async def health_check_handler(
    # cache: Cache = Depends(
    # dependency=get_cache,
    # ),
    session: AsyncSession = Depends(
        dependency=get_session,
    ),
) -> dict[str, bool]:
    # try:
    #     await cache.ping()
    # except Exception:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Cache connection error",
    #     )

    try:
        await session.connection()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DB connection error",
        )

    return {
        "status": True,
    }


async def unicorn_exception_handler(
    request: Request,
    exception: Exception,
) -> ORJSONResponse:
    status_code: int
    detail: str

    if isinstance(exception, HTTPException):
        status_code = exception.status_code
        detail = exception.detail
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        detail = HTTPStatus(status_code).phrase

    return ORJSONResponse(
        status_code=status_code,
        content={
            "status_code": status_code,
            "detail": detail,
        },
    )


async def startup() -> None:
    rabbitmq: RabbitMQ = get_rabbitmq()

    await init_db()
    await rabbitmq.connect()


async def shutdown() -> None:
    rabbitmq: RabbitMQ = get_rabbitmq()

    await rabbitmq.close_connections()
    await close_connection()


def get_application() -> FastAPI:
    project_name: str = settings.app_settings.docs_name.replace("-", " ").capitalize()

    app: FastAPI = FastAPI(
        title=project_name,
        default_response_class=ORJSONResponse,
        middleware=middleware,
        version=settings.app_settings.docs_version,
        docs_url=None,
        openapi_url=None,
        debug=IS_DEBUG,
    )

    app.add_exception_handler(
        exc_class_or_status_code=Exception,
        handler=unicorn_exception_handler,
    )

    app.add_event_handler(
        event_type="startup",
        func=startup,
    )

    app.add_event_handler(
        event_type="shutdown",
        func=shutdown,
    )

    """app.add_api_route(
        path="/health",
        methods=[
            "GET",
        ],
        include_in_schema=False,
        endpoint=health(
            conditions=[
                health_check_handler,
            ],
        ),
    )"""

    setup_docs(
        app=app,
        version="v2",
        project_name=project_name,
        service_name=settings.app_settings.service_name,
        routes=[route for router in v3_routers for route in router.routes],
    )

    for router in v3_routers:
        setup_router(
            app=app,
            router=router,
            version=getattr(router, "version"),
            service_name=getattr(router, "service_name"),
        )

    return app


app: FastAPI = get_application()

if __name__ == "__main__":
    run(
        app=app,
        host=settings.app_settings.wsgi_host,
        port=int(settings.app_settings.wsgi_port),
        use_colors=True,
    )
