from asyncio import run
from logging import config as logging_config
from logging import error, info
from sys import exit
from time import sleep
from typing import Any

from asyncpg import Connection, connect
from asyncpg.exceptions import InvalidCatalogNameError

from app.core.config import settings
from app.core.logger import get_logging_config

log_config: dict[str, Any] = get_logging_config(
    log_level=settings.app_settings.log_level,
)

logging_config.dictConfig(
    config=log_config,
)


async def get_connection(
    db_name: str | None = None,
) -> Connection:
    dsn: str = "postgresql://{}:{}@{}:{}".format(
        settings.postgres_settings.username,
        settings.postgres_settings.password,
        settings.postgres_settings.host,
        settings.postgres_settings.port,
    )

    if db_name:
        dsn += f"/{db_name}"

    info(f"Connection dsn: {dsn}")
    connection = await connect(
        dsn=dsn,
    )
    return connection


async def create_database(
    connection: Connection,
    db_name: str,
) -> None:
    info(f"Creating database: {db_name}")
    if not await connection.fetchrow(
        query=f"""
        SELECT
            1
        FROM pg_database
        WHERE datname = '{db_name}';
        """,
    ):
        await connection.execute(
            query=f"""
            CREATE DATABASE {db_name};
            """,
        )


async def create_schema(
    connection: Connection,
    schema_name: str,
) -> None:
    info(f"Creating schema {schema_name}")
    if not await connection.fetchrow(
        query=f"""
        SELECT
            1
        FROM information_schema.schemata
        WHERE schema_name = '{schema_name}';
        """,
    ):
        await connection.execute(
            query=f"""
            CREATE SCHEMA {schema_name};
            """,
        )


async def main() -> None:
    retries: int = 100
    delay: float = 10

    while True:
        db_name: str = settings.postgres_settings.db_name
        schema_name: str = settings.postgres_settings.schema_name

        connection: Connection | None = None

        try:
            connection = await get_connection(
                db_name=db_name,
            )

            await create_schema(
                connection=connection,
                schema_name=schema_name,
            )
        except OSError:
            retries -= 1

            if not retries:
                error("PostgreSQL connection error")
                exit(1)

            info(f"Waiting for PostgreSQL, {retries} remaining attempt...")
            sleep(delay)
        except InvalidCatalogNameError:
            connection = await get_connection()

            await create_database(
                connection=connection,
                db_name=db_name,
            )

            await connection.close()
        else:
            await connection.close()

            exit(0)


if __name__ == "__main__":
    run(
        main=main(),
    )
