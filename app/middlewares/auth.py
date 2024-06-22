from logging import error
from typing import Any

from fastapi import status
from fastapi.exceptions import HTTPException
from fastapi.param_functions import Security
from fastapi.requests import Request as IncomingRequest
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.api_key import APIKeyHeader
from httpx import AsyncClient, Request, Response

from app.core.config import settings


def api_key_auth(
    api_key: str = Security(
        dependency=APIKeyHeader(
            name="X-API-KEY",
            auto_error=False,
        ),
    ),
) -> None:
    if api_key != settings.app_settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
        )


class JWTBearer(HTTPBearer):
    def __init__(
        self,
        auto_error: bool = True,
    ) -> None:
        super(
            JWTBearer,
            self,
        ).__init__(
            auto_error=auto_error,
        )

    async def __call__(
        self,
        request: IncomingRequest,
    ) -> None:
        credentials: HTTPAuthorizationCredentials | None = await super(
            JWTBearer,
            self,
        ).__call__(
            request,
        )

        setattr(request, "user_id", None)
        setattr(request, "phone", None)

        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=403,
                    detail="Invalid authentication scheme",
                )

            if not await self.verify_jwt(
                request=request,
                token=credentials.credentials,
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Token invalid or expired",
                )
        else:
            raise HTTPException(
                status_code=403,
                detail="Invalid authorization code",
            )

    async def verify_jwt(self, token: str, request: IncomingRequest) -> bool:

        try:
            async with AsyncClient() as client:
                response: Response = await client.send(
                    request=Request(
                        method="GET", url=settings.ecom_settings.auth_url, headers={"Authorization": f"Bearer {token}"}
                    )
                )

                response.raise_for_status()

                result: dict[str, Any] = response.json()

                user_id: str | None = result.get("user_id")
                phone: str | None = result.get("phone")

                if not user_id or not phone:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Не удалось получить ID пользователя или телефон по переданному токену",
                    )

                setattr(request, "user_id", user_id)
                setattr(request, "phone", phone)
            return True
        except Exception as err:
            error(f"Ошибка проверки токена: {err}")
            return False


class SellerCheck(HTTPBearer):
    def __init__(self, auto_error: bool = True, description: str = "Provide user token") -> None:
        super(
            SellerCheck,
            self,
        ).__init__(
            auto_error=auto_error,
            description=description,
        )

    async def __call__(
        self,
        request: IncomingRequest,
    ) -> None:
        credentials: HTTPAuthorizationCredentials | None = await super(
            SellerCheck,
            self,
        ).__call__(
            request,
        )
        setattr(request, "seller_id", None)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=403,
                    detail="Invalid authentication scheme",
                )

            await self.verify_seller(token=credentials.credentials, request=request)
        else:
            raise HTTPException(
                status_code=403,
                detail="Invalid authorization code",
            )

    async def verify_seller(
        self,
        token: str,
        request: IncomingRequest,
    ) -> bool:
        try:
            async with AsyncClient() as client:
                response: Response = await client.send(
                    request=Request(
                        method="GET",
                        url=settings.ecom_settings.seller_check_url,
                        headers={"Authorization": f"Bearer {token}"},
                    )
                )
                if not response.is_success:
                    error_detail: str | None = response.json().get("detail")
                    raise Exception(error_detail)
                seller_id: str | None = response.json()
                setattr(request, "seller_id", seller_id)
            return True
        except Exception as err:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Ошибка проверки токена: {err}")
