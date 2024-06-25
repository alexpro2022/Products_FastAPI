from typing import Any, TypeAlias
from uuid import UUID

# from sqlalchemy import Insert, Select, Update, delete, insert, select, update
import sqlalchemy as sa
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

IdType: TypeAlias = int | UUID
ModelType: TypeAlias = Any
StmtType: TypeAlias = sa.Insert | sa.Select | sa.Update

MSG_OBJECT_NOT_FOUND = "Объект не найден"


async def fetch_one(session: AsyncSession, stmt: StmtType):
    result = await session.scalars(stmt)
    await session.commit()
    return result.first()


async def create(session: AsyncSession, model: ModelType, **create_data) -> ModelType:
    stmt = sa.insert(model).values(**create_data).returning(model)
    return await fetch_one(session, stmt)


async def update(session: AsyncSession, model: ModelType, id: IdType, **update_data) -> ModelType:
    stmt = sa.update(model).where(model.id == id).values(**update_data).returning(model)
    return await fetch_one(session, stmt)


async def delete(session: AsyncSession, model: ModelType, id: IdType, **update_data) -> ModelType:
    stmt = sa.delete(model).where(model.id == id).returning(model)
    return await fetch_one(session, stmt)


async def get(
    session: AsyncSession,
    model: ModelType,
    exception: bool = False,
    msg: str = MSG_OBJECT_NOT_FOUND,
    fetch_one: bool = False,
    **filter_data,
) -> ModelType | list[ModelType]:
    stmt = sa.select(model).filter_by(**filter_data)
    result = await session.scalars(stmt)
    res = result.first() if filter_data.get("id") or fetch_one else result.all()
    if not res and exception:
        raise HTTPException(status.HTTP_404_NOT_FOUND, msg)
    return res


async def get_all(session: AsyncSession, model: ModelType):
    return await get(session, model)


async def get_or_404(session: AsyncSession, model: ModelType, id: IdType):
    return await get(session, model, exception=True, id=id)
