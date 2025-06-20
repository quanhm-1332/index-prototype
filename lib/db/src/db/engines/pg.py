from typing import Self

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)

import logfire
from structlog.stdlib import BoundLogger

from logs import get_logger

from ..settings import PostgresSettings


_engine = None


class Base(AsyncAttrs, DeclarativeBase):
    pass


async def start_db(
    username: str,
    password: str,
    host: str,
    port: int,
    logger: BoundLogger = get_logger("postgres.engine"),
):
    global _engine
    if not _engine:
        await logger.ainfo("Starting postgres engine")
        from sqlalchemy import URL

        _url = URL.create(
            "postgresql+psycopg",
            username=username,
            password=password,
            host=host,
            port=port,
        )

        engine = create_async_engine(_url)

        logfire.instrument_sqlalchemy(engine)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _engine = engine
        return engine
    await logger.ainfo("Postgres engine already started")
    return _engine


class PostgresClient:
    def __init__(
        self,
        engine: AsyncEngine,
        logger: BoundLogger,
    ):
        self._engine = engine
        self._session = async_sessionmaker(self._engine, expire_on_commit=False)
        self._logger = logger
        self._logger.info("Postgres client initialized")

    @classmethod
    async def init(
        cls,
        settings: PostgresSettings,
        logger: BoundLogger = get_logger("postgres.client"),
    ) -> Self:
        engine = await start_db(
            settings.username,
            settings.password.get_secret_value(),
            settings.host,
            settings.port,
        )
        return cls(engine, logger)

    @property
    def get_session(self):
        return self._session

    async def close(self):
        await self._engine.dispose()
        await self._logger.ainfo("Postgres client closed")
