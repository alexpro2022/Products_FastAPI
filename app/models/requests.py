from typing import Callable, ClassVar

from pydantic.networks import IPvAnyAddress
from sqlalchemy.sql import expression
from sqlalchemy_utils.types.ip_address import IPAddressType
from sqlmodel import Column, String
from sqlmodel.main import Field

from app.db import metadata
from app.models.base import IDMixin, TimestampsMixin


class RequestInfo(IDMixin, TimestampsMixin, table=True):
    __tablename__: ClassVar[str | Callable[..., str]] = "request_info"
    __table_args__: dict[str, str | None] = {"schema": metadata.schema}
    user_agent: str = Field(
        description="""
        User Agent
        """,
        sa_column=Column(
            String,
            nullable=True,
            server_default=expression.null(),
        ),
    )
    cookie: str | None = Field(
        description="""
        Cookie
        """,
        sa_column=Column(
            String,
            nullable=True,
            server_default=expression.null(),
        ),
    )
    real_ip: IPvAnyAddress | None = Field(
        default=None,
        description="""
        IP Address
        """,
        sa_column=Column(
            IPAddressType,
            nullable=True,
            index=True,
        ),
    )
    referer: str | None = Field(
        default="sarawan.ru",
        description="""
        Наименование портала
        """,
        sa_column=Column(String(255), nullable=True),
    )
