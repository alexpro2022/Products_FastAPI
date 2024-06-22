from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Uuid
from sqlalchemy.sql import func, text
from sqlmodel import Field, SQLModel


class IDMixin(SQLModel):
    id: UUID = Field(
        description="Primary model key",
        default_factory=uuid4,
        sa_type=Uuid(as_uuid=True),
        sa_column_kwargs={"server_default": text("gen_random_uuid()"), "unique": True},
        nullable=False,
        primary_key=True,
        index=True,
    )
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": str(uuid4()),
                }
            ]
        }
    }


class TimestampsMixin(SQLModel):
    created_at: datetime | None = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
    )
    updated_at: datetime | None = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),
            "onupdate": func.now(),
        },
        nullable=False,
    )
    model_config = {
        "json_schema_extra": {
            "examples": [{"created_at": datetime.utcnow().isoformat(), "updated_at": datetime.utcnow().isoformat()}]
        }
    }
