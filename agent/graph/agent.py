"""M4 LangGraph Agent — StateGraph + MemorySaver + 跨轮 thread_id。

与 ``agent/agent.py``（M2 for 循环）并列，便于对比学习。
工具与 prompt 仍复用 ``agent/skills``、``agent/promt``。
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent.agent import Agent as ClassicAgent
from agent.agent.skills import SKILL_TOOLS, discover_skill_modules
from agent.graph.graph import build_agent_graph
from server.db.session import Database

MAX_TOOL_ROUNDS = 5

logger = logging.getLogger("billmind.graph.agent")

_COMPILED_GRAPH: Any | None = None
_RECURSION_LIMIT: int = MAX_TOOL_ROUNDS * 2 + 1


def extract_reply(messages: list) -> str:
    """从图输出 messages 中取最后一条 AI 文本回复。"""
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.tool_calls:
            content = message.content
            return content if isinstance(content, str) else str(content)
    if messages:
        last = messages[-1]
        if isinstance(last, AIMessage):
            content = last.content
            return content if isinstance(content, str) else str(content)
    return "未能生成回复，请重试。"

class Agent:
    """LangGraph 版 Agent — init / invoke / parse_image（视觉链委托 M2）。"""

    @classmethod
    def init(cls) -> None:
        """加载 skills 并编译 LangGraph。"""
        global _COMPILED_GRAPH, _RECURSION_LIMIT

        discover_skill_modules(Database.get().async_session_factory)
        tools = list(SKILL_TOOLS.values())
        checkpointer = MemorySaver()
        _COMPILED_GRAPH, _RECURSION_LIMIT = build_agent_graph(
            tools,
            checkpointer,
            max_tool_rounds=MAX_TOOL_ROUNDS,
        )
        logger.info("graph agent skills loaded: %s", ", ".join(SKILL_TOOLS))

    @classmethod
    async def invoke(
        cls,
        message: str,
        *,
        account_id: int,
        db: AsyncSession | None = None,  # noqa: ARG003
        thread_id: str | None = None,
        debug: bool = False,
    ) -> tuple[str, str]:
        """处理用户消息，返回 (回复, thread_id)。历史由 checkpointer 按 thread_id 累积。"""
        del db
        logger.info("input: %s", message)

        if _COMPILED_GRAPH is None:
            raise RuntimeError("Graph Agent 未初始化，请先调用 Agent.init()")

        effective_thread_id = thread_id or str(uuid4())
        config = {
            "configurable": {
                "thread_id": effective_thread_id,
                "debug": debug,
                "account_id": account_id,
            },
            "recursion_limit": _RECURSION_LIMIT,
        }

        result = await _COMPILED_GRAPH.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config=config,
        )
        reply = extract_reply(result["messages"])
        logger.info("output: %s", reply)
        return reply, effective_thread_id

    @classmethod
    async def parse_image(cls, image_data_url: str) -> str:
        """视觉链与 M2 相同，委托 ``agent.agent.Agent``。"""
        return await ClassicAgent.parse_image(image_data_url)
