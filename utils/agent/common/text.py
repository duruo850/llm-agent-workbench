from typing import Any

from langchain_core.messages import AIMessage, ToolMessage


def extract_tool_names(messages: list) -> list[str]:
    """从图输出 messages 中提取已执行的工具名（``ToolMessage.name``）。"""
    return [message.name for message in messages if isinstance(message, ToolMessage) and message.name]


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


def tool_result_text(output: Any) -> str:
    """把 on_tool_end 的 output 统一成字符串，便于判断「有无结果」。"""
    if output is None:
        return ""
    if isinstance(output, ToolMessage):
        content = output.content
        return content if isinstance(content, str) else str(content)
    if isinstance(output, str):
        return output
    content = getattr(output, "content", None)
    if content is not None:
        return content if isinstance(content, str) else str(content)
    return str(output)
