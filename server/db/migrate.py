"""启动时数据库状态检查与 Alembic 迁移。"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from common.env import get_database_url, load_env

logger = logging.getLogger("billmind.db")

_ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
_REQUIRED_TABLES = ("categories", "budgets", "transactions")


def _alembic_config() -> Config:
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", get_database_url())
    return cfg


async def check_db_status(engine: AsyncEngine) -> dict[str, bool]:
    """检查数据库连接与核心表是否就绪。"""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
        tables = await conn.run_sync(lambda sync_conn: set(inspect(sync_conn).get_table_names()))
    return {
        "connected": True,
        "ready": all(table in tables for table in _REQUIRED_TABLES),
        "has_alembic_version": "alembic_version" in tables,
    }


def migrate() -> None:
    """执行 ``alembic upgrade head``：空库建表，已有库补齐未应用的迁移。"""
    load_env()
    logger.info("running alembic upgrade head")
    command.upgrade(_alembic_config(), "head")
    logger.info("database schema up to date")


async def migrate_on_startup(engine: AsyncEngine) -> None:
    """应用启动时调用：库不可达则失败；表未就绪则自动迁移。"""
    import server.model.budget  # noqa: F401
    import server.model.category  # noqa: F401
    import server.model.transaction  # noqa: F401

    try:
        status = await check_db_status(engine)
    except Exception as exc:
        logger.error("database unreachable: %s", exc)
        raise

    if status["ready"]:
        logger.info("database schema ready")
        return

    logger.warning(
        "database not ready (alembic_version=%s), applying migrations",
        status["has_alembic_version"],
    )
    await asyncio.to_thread(migrate)
