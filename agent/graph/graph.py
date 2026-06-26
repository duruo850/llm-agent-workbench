"""
LangGraph ReAct 状态图 — agent 节点 + ToolNode + checkpointer。
是一个对LLM编排的有向图，基于有向图的节点和边结构,支持复杂的循环和分支管理
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition

from agent.agent.promt.system import system_prompt
from common.llm import LLMCapability, LLMProvider, get_openai_chat_llm

logger = logging.getLogger("billmind.graph")

RECURSION_LIMIT_FACTOR = 2


def make_agent_node(llm: Any, tools_list: list[BaseTool]):
    """工厂：返回 LangGraph **agent** 节点。"""

    async def agent_node(
        state: MessagesState, config: RunnableConfig
    ) -> dict[str, Any]:
        messages = list(state["messages"])
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=system_prompt(tools_list)))

        debug = bool(config.get("configurable", {}).get("debug"))
        response = await llm.ainvoke(messages, config)
        if response.tool_calls:
            logger.info("llm tool_calls: %s", response.tool_calls)
            if debug:
                print(f"\n▸ LLM tool_calls: {response.tool_calls}")
        else:
            logger.info("llm content: %s", response.content)
            if debug:
                print(f"\n▸ LLM content: {response.content}")
        return {"messages": [response]}

    return agent_node


def build_agent_graph(
    tools: list[BaseTool],
    checkpointer: BaseCheckpointSaver,
    *,
    max_tool_rounds: int,
):
    """构建并 compile ReAct 图：START → agent → (tools | END)。"""
    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        temperature=0,
    ).bind_tools(tools)

    agent_node = make_agent_node(llm, tools)
    tool_node = ToolNode(tools)

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    recursion_limit = max_tool_rounds * RECURSION_LIMIT_FACTOR + 1
    return graph.compile(checkpointer=checkpointer), recursion_limit

