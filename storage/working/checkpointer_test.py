"""AsyncPostgresSaver 单测 - 依赖已启动的 PostgreSQL."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from sqlalchemy import text

from storage.working.checkpointer import (
    get_checkpointer,
    init_checkpointer,
    shutdown_checkpointer,
)
from common.env import get_database_url, load_env
from server.db.session import Database


def _db_reachable() -> bool:
    """当前环境能否连上 PostgreSQL (测试 skip 判断)."""
    load_env()
    try:
        Database.init(get_database_url())
        engine = Database.get().engine
        return engine is not None
    except Exception:
        return False


@pytest.fixture
def require_postgres() -> None:
    if not _db_reachable():
        pytest.skip("PostgreSQL 不可用, 跳过 checkpointer 测试")


async def _checkpoints_table_exists() -> bool:
    """``init_checkpointer`` 后 ``checkpoints`` 表是否已创建."""
    Database.init(get_database_url())
    async with Database.get().engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'checkpoints'"
            )
        )
        return result.scalar() is not None


def test_init_checkpointer_creates_checkpoints_table(require_postgres: None) -> None:
    """``init_checkpointer`` 应在 PG 中建好 LangGraph checkpoint 表."""

    async def _run() -> None:
        await shutdown_checkpointer()
        await init_checkpointer()
        assert await _checkpoints_table_exists()
        await shutdown_checkpointer()

    asyncio.run(_run())


def test_checkpoint_survives_reinit(require_postgres: None) -> None:
    """模拟进程重启: shutdown 后重新 init, 同 thread_id 仍有历史."""

    async def _run() -> None:
        thread_id = f"test-restart-{uuid.uuid4().hex[:8]}"

        async def echo_node(state: MessagesState) -> dict:
            last = state["messages"][-1]
            text_content = last.content if isinstance(last.content, str) else str(last.content)
            return {"messages": [AIMessage(content=f"echo:{text_content}")]}

        builder = StateGraph(MessagesState)
        builder.add_node("echo", echo_node)
        builder.add_edge(START, "echo")
        builder.add_edge("echo", END)

        await shutdown_checkpointer()
        await init_checkpointer()
        graph = builder.compile(checkpointer=get_checkpointer())
        config = {"configurable": {"thread_id": thread_id}}
        await graph.ainvoke({"messages": [HumanMessage(content="hello")]}, config=config)

        await shutdown_checkpointer()
        await init_checkpointer()
        graph2 = builder.compile(checkpointer=get_checkpointer())
        result = await graph2.ainvoke(
            {"messages": [HumanMessage(content="follow-up")]}, config=config
        )
        # 历史 2 条 + 本轮 human + echo = 至少 4
        assert len(result["messages"]) >= 4
        await shutdown_checkpointer()

    asyncio.run(_run())
