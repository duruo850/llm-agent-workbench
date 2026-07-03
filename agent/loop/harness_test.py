"""Loop Harness 单元测试 — 用伪造事件流验证 Harness，无需真实 LLM / LangGraph。

测试策略：

- 不启动 API、不调用 DeepSeek
- ``_FakeGraph`` 模拟 ``astream_events``，按序 yield 预设事件 dict
- 覆盖：无结果判定、token 解析、步数递增、同工具 streak 兜底、should_stop 钩子
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from utils.agent.common.result import is_no_tool_result
from utils.agent.common.text import extract_reply
from utils.agent.common.token import extract_token_usage
from agent.loop.harness import LoopHarness
from agent.loop.hooks import LoopHooks, LoopStepMetrics
from agent.loop.policy import (
    RECURSION_LIMIT,
    SAME_TOOL_GIVE_UP_REPLY,
    SAME_TOOL_NO_RESULT_LIMIT,
)


def test_is_no_tool_result() -> None:
    """边界：空值、空 JSON、error 字段、正常 JSON 的判定。"""
    assert is_no_tool_result("") is True
    assert is_no_tool_result("   ") is True
    assert is_no_tool_result("{}") is True
    assert is_no_tool_result("[]") is True
    assert is_no_tool_result('{"error": "not found"}') is True
    assert is_no_tool_result('{"amount": 12.5}') is False
    assert is_no_tool_result(ToolMessage(content="", tool_call_id="1", name="t")) is True
    assert is_no_tool_result(ToolMessage(content="ok", tool_call_id="1", name="t")) is False


def test_extract_token_usage_from_usage_metadata() -> None:
    """从 AIMessage.usage_metadata.total_tokens 读取。"""
    event = {
        "data": {
            "output": AIMessage(
                content="hi",
                usage_metadata={
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "total_tokens": 15,
                },
            )
        }
    }
    assert extract_token_usage(event) == 15


def test_extract_token_usage_missing_metadata() -> None:
    """无 metadata 时返回 0，不抛异常。"""
    event = {"data": {"output": AIMessage(content="hi")}}
    assert extract_token_usage(event) == 0


class _FakeGraph:
    """最小 LangGraph 替身 — 只实现 Harness 需要的 astream_events。"""

    def __init__(self, events: list[dict[str, Any]]) -> None:
        self._events = events

    async def astream_events(self, _input: Any, *, config: dict[str, Any], version: str):
        del config, version
        for event in self._events:
            yield event


def _tool_end(name: str, content: str) -> dict[str, Any]:
    """构造 on_tool_end 事件。"""
    return {
        "event": "on_tool_end",
        "name": name,
        "data": {
            "output": ToolMessage(content=content, tool_call_id="c1", name=name),
        },
    }


def _model_end(tokens: int = 0) -> dict[str, Any]:
    """构造 on_chat_model_end 事件。"""
    usage = {"input_tokens": tokens, "output_tokens": 0, "total_tokens": tokens}
    return {
        "event": "on_chat_model_end",
        "name": "ChatOpenAI",
        "data": {"output": AIMessage(content="x", usage_metadata=usage)},
    }


def _graph_end(messages: list | None = None) -> dict[str, Any]:
    """构造图结束事件，用于提供最终 messages。"""
    return {
        "event": "on_chain_end",
        "name": "LangGraph",
        "data": {"output": {"messages": messages or [AIMessage(content="done")]}},
    }


def test_harness_increments_steps_and_tokens() -> None:
    """一步 LLM + 一步工具 + 一步 LLM → total_steps=3，token 累加正确。"""
    graph = _FakeGraph(
        [
            _model_end(12),
            _tool_end("query_transactions", '{"rows": []}'),
            _model_end(8),
            _graph_end(),
        ]
    )

    async def _run() -> tuple[int, int]:
        steps: list[LoopStepMetrics] = []

        async def on_step(metrics: LoopStepMetrics) -> None:
            steps.append(metrics)

        result = await LoopHarness.invoke_turn(
            graph,
            {"messages": []},
            {"recursion_limit": RECURSION_LIMIT},
            turn_id="turn-1",
            hooks=LoopHooks(on_step=on_step),
        )
        return result.total_steps, result.total_tokens

    total_steps, total_tokens = asyncio.run(_run())
    assert total_steps == 3
    assert total_tokens == 20


def test_harness_same_tool_no_result_give_up() -> None:
    """同一工具连续 SAME_TOOL_NO_RESULT_LIMIT 次空返回 → 中断并写入兜底 messages。"""
    events = []
    for _ in range(SAME_TOOL_NO_RESULT_LIMIT):
        events.append(_model_end(1))
        events.append(_tool_end("query_transactions", ""))
    graph = _FakeGraph(events)

    async def _run() -> tuple[str | None, str]:
        result = await LoopHarness.invoke_turn(
            graph,
            {"messages": []},
            {"recursion_limit": RECURSION_LIMIT},
            turn_id="turn-give-up",
        )
        return result.stopped_reason, extract_reply(result.messages)

    stopped_reason, reply = asyncio.run(_run())
    assert stopped_reason == "same_tool_no_result"
    assert reply == SAME_TOOL_GIVE_UP_REPLY


def test_harness_should_stop_hook() -> None:
    """自定义 should_stop：第 2 步即中断，stopped_reason=recursion_limit。"""
    graph = _FakeGraph([_model_end(1), _model_end(1), _graph_end()])

    def should_stop(metrics: LoopStepMetrics) -> bool:
        return metrics.step_count >= 2

    async def _run() -> str | None:
        result = await LoopHarness.invoke_turn(
            graph,
            {"messages": []},
            {"recursion_limit": RECURSION_LIMIT},
            turn_id="turn-stop",
            hooks=LoopHooks(should_stop=should_stop),
        )
        return result.stopped_reason

    assert asyncio.run(_run()) == "recursion_limit"
