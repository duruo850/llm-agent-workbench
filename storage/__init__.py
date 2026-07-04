"""Storage — 持久化总入口 (PostgreSQL CRUD / Milvus RAG / LangGraph checkpointer)."""

from __future__ import annotations

from storage import postgres, rag, working

__all__ = ["init", "shutdown", "postgres", "rag", "working"]


async def init() -> None:
    """初始化 Working Memory checkpointer 与 PG 异步落库 Controller。"""
    await working.init_checkpointer()
    from storage.postgres.controller import init_controllers

    init_controllers()


async def shutdown() -> None:
    """关闭 PG 异步落库 Controller 与 checkpointer 连接池."""
    from storage.postgres.controller import shutdown_controllers

    shutdown_controllers()
    await working.shutdown_checkpointer()
