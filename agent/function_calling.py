"""Function Calling 执行层 — 将 AIMessage.tool_calls 转为 ToolMessage。"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import BaseTool

logger = logging.getLogger("billmind.agent")


async def execute_tool_calls(
    ai_message: AIMessage,
    tools_map: dict[str, BaseTool],
    *,
    debug: bool = False,
) -> list[ToolMessage]:
    """执行模型输出的 tool_calls，返回 ToolMessage 列表。"""
    tool_messages: list[ToolMessage] = []
    for tool_call in ai_message.tool_calls:
        name = tool_call["name"]
        args: dict[str, Any] = tool_call["args"]
        tool_call_id = tool_call["id"]
        logger.info("tool invoke: %s(%s)", name, args)
        if debug:
            print(f"  ▸ 工具调用: {name}({args})")
        tool = tools_map.get(name)
        if tool is None:
            content = f'{{"error": true, "detail": "未知工具: {name}"}}'
        else:
            content = await tool.ainvoke(args)
        preview = content[:200] + ("..." if len(content) > 200 else "")
        logger.info("tool result: %s", preview)
        if debug:
            print(f"    返回: {preview}")
        tool_messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
    return tool_messages
