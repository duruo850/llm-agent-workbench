"""Working Memory - AsyncPostgresSaver 生命周期.

连接: 复用 ``DATABASE_URL`` 同一 PostgreSQL (与 categories / transactions 等业务表同库)

表 (``init_checkpointer()`` -> ``setup()`` 自动建表, 不走 Alembic):
  - ``checkpoints``: 主索引; ``thread_id``, ``checkpoint_id``, ``checkpoint`` (JSONB 元数据), ``metadata``
  - ``checkpoint_blobs``: 大对象; ``messages`` 等 channel 的 msgpack 二进制
  - ``checkpoint_writes``: 每步图执行写了哪些 channel
  - ``checkpoint_migrations``: LangGraph checkpoint schema 版本

存什么 (Agent 工作记忆, 非给人看的聊天记录):
  - LangGraph 图 state 快照: 主要是 ``messages`` 列表 (HumanMessage / AIMessage / ToolMessage 序列化)
  - 图元数据: 第几步, 节点, 时间戳, parent checkpoint 等
  - 按 ``configurable.thread_id`` 分区; 同 thread 下次 invoke 可恢复上下文 ("刚才那笔...")

能否直接看懂:
  - ``checkpoints`` 的 JSONB 只能看到结构/元数据, 正文不在此
  - ``checkpoint_blobs`` 为 msgpack 二进制, SQL 里只能看到零散文本片段, 不适合当聊天历史读
  - 可读明文请查业务表 ``conversations`` / ``chat_messages`` 或
    ``GET /conversations/{thread_id}/messages``

与 chat 表分工:
  - checkpointer = Agent 跨轮推理用的 state 备份 (机器读)
  - chat_messages = 每轮 user/assistant 明文 (人读 / Web 展示)

开发/测试对照见 ``docs/knowledge/memory-os.md`` § MemorySaver (进程内 ``MemorySaver`` 仅单测 mock).
"""

from __future__ import annotations

import logging

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from common.env import get_database_url

logger = logging.getLogger("billmind.storage.working")

_CONNECTION_KWARGS = {
    "autocommit": True,
    "prepare_threshold": 0,
    "row_factory": dict_row,
}

_pool: AsyncConnectionPool | None = None
_checkpointer: AsyncPostgresSaver | None = None


def _to_psycopg_dsn(database_url: str) -> str:
    """将 SQLAlchemy async DSN 转为 psycopg 可用的 ``postgresql://``."""
    if database_url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + database_url.removeprefix("postgresql+asyncpg://")
    if database_url.startswith("postgres+asyncpg://"):
        return "postgresql://" + database_url.removeprefix("postgres+asyncpg://")
    return database_url


async def init_checkpointer() -> None:
    """连接 PostgreSQL, 创建 checkpointer 表并缓存单例."""
    global _pool, _checkpointer

    if _checkpointer is not None:
        return

    dsn = _to_psycopg_dsn(get_database_url())
    _pool = AsyncConnectionPool(dsn, kwargs=_CONNECTION_KWARGS, open=False)
    await _pool.open()
    _checkpointer = AsyncPostgresSaver(_pool)
    await _checkpointer.setup()
    logger.info("AsyncPostgresSaver ready (dsn host only logged)")
    logger.debug("checkpointer dsn=%s", dsn.split("@")[-1] if "@" in dsn else dsn)


async def shutdown_checkpointer() -> None:
    """关闭连接池并释放 checkpointer."""
    global _pool, _checkpointer

    _checkpointer = None
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("AsyncPostgresSaver shut down")


def get_checkpointer() -> AsyncPostgresSaver:
    """供 ``build_agent_graph`` 编译使用."""
    if _checkpointer is None:
        raise RuntimeError("Checkpointer 未初始化, 请先调用 init_checkpointer()")
    return _checkpointer


def is_checkpointer_ready() -> bool:
    """checkpointer 是否已完成 ``init_checkpointer()``."""
    return _checkpointer is not None


def get_checkpointer_pool() -> AsyncConnectionPool | None:
    """测试用: 访问底层连接池."""
    return _pool
