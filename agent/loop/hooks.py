"""Loop 可挂载钩子 — 让调用方在不改 Harness 核心的前提下扩展行为。

设计意图：

- Harness 只负责「读事件 → 算指标 → 判断要不要停」
- 落库、打日志、自定义超轮次策略等，通过钩子注入，保持 Harness 可测试、可复用

在 ``invoke_v2`` 中的典型用法::

    async def on_step(metrics: LoopStepMetrics) -> None:
        await agent_loop_step_service.create_step(db, ...)

    LoopHarness.run(..., hooks=LoopHooks(on_step=on_step))
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from agent.loop.policy import RECURSION_LIMIT



def default_should_stop(metrics: LoopStepMetrics) -> bool:
    """默认超轮次策略：步数达到 RECURSION_LIMIT 时停止。"""
    return metrics.step_count >= RECURSION_LIMIT


@dataclass
class LoopStepMetrics:
    """单步循环指标 — 每发生一次 LLM 调用或工具执行，Harness 构造一份。"""

    step_count: int  # 本轮 invoke 内从 1 递增（非 LangGraph 全局递归深度）
    token_usage: int  # 该步 LLM token 合计；工具步为 0
    node_name: str | None  # 事件来源节点，如 ``ChatOpenAI``、``query_transactions``
    tool_name: str | None  # 仅 ``on_tool_end`` 时有值，与 node_name 相同


@dataclass
class LoopHooks:
    """循环钩子集合 — 均为可选，未提供时使用 Harness 内置默认行为。"""

    # 每步结束后异步回调（invoke_v2 用它写 agent_loop_steps + 打日志）
    on_step: Callable[[LoopStepMetrics], Awaitable[None]] | None = None

    # 返回 True 时主动中断循环；默认实现为 step_count >= RECURSION_LIMIT
    should_stop: Callable[[LoopStepMetrics], bool] | None = default_should_stop


