from fastapi.param_functions import Header
from fastapi.requests import Request
from pydantic.networks import IPvAnyAddress

from app.models.requests import RequestInfo


def set_request_info(
    request: Request,
    user_agent: str = Header(
        default=None,
        include_in_schema=False,
    ),
    cookie: str = Header(
        default=None,
        include_in_schema=False,
    ),
    real_ip: IPvAnyAddress | None = Header(
        default=None,
        alias="x-real-ip",
        include_in_schema=False,
    ),
    referer: str | None = Header(default=None, include_in_schema=False),
) -> None:
    request_info: RequestInfo = RequestInfo(user_agent=user_agent, cookie=cookie, real_ip=real_ip, referer=referer)

    setattr(request, "request_info", request_info)
