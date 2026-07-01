"""Working Memory - LangGraph 单会话短期 state.

存储: PostgreSQL (复用 ``DATABASE_URL``, LangGraph 自建表, 不走 Alembic)
表: ``checkpoints``, ``checkpoint_blobs``, ``checkpoint_writes``, ``checkpoint_migrations``
记录数据:
  - 图 state 快照 (``messages`` 等 channel 序列化 blob)
  - 按 ``configurable.thread_id`` 分区; 与 ``account_id`` 业务隔离互补
  - 供 Agent 多轮 ReAct 跨轮引用 ("刚才那笔...")
状态: M9 已实现 (``AsyncPostgresSaver``)
"""

from storage.working.checkpointer import (
    get_checkpointer,
    init_checkpointer,
    is_checkpointer_ready,
    shutdown_checkpointer,
)

__all__ = [
    "get_checkpointer",
    "init_checkpointer",
    "is_checkpointer_ready",
    "shutdown_checkpointer",
]
