"""Storage — 持久化总入口 (PostgreSQL CRUD / Milvus RAG / LangGraph checkpointer)."""

from __future__ import annotations

from storage import postgres, rag, working

__all__ = ["init", "shutdown", "postgres", "rag", "working"]


async def init() -> None:
    """初始化 Working Memory checkpointer."""
    await working.init_checkpointer()


async def shutdown() -> None:
    """关闭 checkpointer 连接池."""
    await working.shutdown_checkpointer()
