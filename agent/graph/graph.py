"""
LangGraph ReAct — 通过 ``create_react_agent`` 接入 MCP / skill tools。
"""

from __future__ import annotations

from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from agent.agent.promt.system import system_prompt
from common.llm import LLMCapability, LLMProvider, get_openai_chat_llm

RECURSION_LIMIT_FACTOR = 2


def build_agent_graph(
    tools: list[BaseTool],
    checkpointer: BaseCheckpointSaver,
    *,
    max_tool_rounds: int,
) -> tuple[CompiledStateGraph, int]:
    """LangGraph 方式：MultiServerMCPClient tools + skills → ``create_react_agent``。"""
    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        temperature=0,
    )
    graph = create_react_agent(
        llm,
        tools,
        prompt=system_prompt(tools),
        checkpointer=checkpointer,
    )
    recursion_limit = max_tool_rounds * RECURSION_LIMIT_FACTOR + 1
    return graph, recursion_limit
