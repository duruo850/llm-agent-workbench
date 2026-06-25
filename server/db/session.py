from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import ClassVar

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """异步数据库连接池单例；``database_url`` 由调用方注入，不在此模块读环境变量。"""

    _instance: ClassVar[Database | None] = None

    def __init__(
        self,
        database_url: str,
        *,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        echo: bool = False,
    ) -> None:
        self.database_url = database_url
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=pool_recycle,
        )
        self.async_session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
        )

    @classmethod
    def init(
        cls,
        database_url: str,
        *,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        echo: bool = False,
    ) -> Database:
        if cls._instance is None:
            cls._instance = cls(
                database_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_recycle=pool_recycle,
                echo=echo,
            )
        return cls._instance

    @classmethod
    def get(cls) -> Database:
        if cls._instance is None:
            raise RuntimeError(
                "Database 未初始化，请先调用 Database.init(database_url)"
            )
        return cls._instance

    async def dispose(self) -> None:
        await self.engine.dispose()

    @classmethod
    def reset(cls) -> None:
        cls._instance = None


def init_db(database_url: str, **pool_kwargs: object) -> Database:
    return Database.init(database_url, **pool_kwargs)  # type: ignore[arg-type]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with Database.get().async_session_factory() as session:
        yield session
