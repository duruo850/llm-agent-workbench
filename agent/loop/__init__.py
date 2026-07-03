"""M10 Loop Engineering — Agent 层循环执行监控与策略。

本包与 ``agent/graph/`` 同级，职责划分：

- ``agent/graph/``：如何**编译** LangGraph（``create_react_agent``、checkpointer）
- ``agent/loop/``：如何**执行并监控**循环（步数、token、硬/软上限、钩子）

典型调用链::

    POST /agent/chat
      → graph/agent.invoke_v2()
      → LoopHarness.run(compiled_graph, ...)
      → on_step 钩子落库 agent_loop_steps

对外统一从此模块导入，避免调用方散落引用子模块路径。
"""

from utils.agent.common.text import extract_reply
from agent.loop.harness import LoopHarness, LoopRunResult, LoopTurnContext
from agent.loop.hooks import LoopHooks, LoopStepMetrics
from agent.loop.policy import (
    RECURSION_LIMIT,
    SAME_TOOL_GIVE_UP_REPLY,
    SAME_TOOL_NO_RESULT_LIMIT,
)
from agent.loop.prompt import LOOP_ENGINEERING_RULES

__all__ = [
    "RECURSION_LIMIT",
    "SAME_TOOL_GIVE_UP_REPLY",
    "SAME_TOOL_NO_RESULT_LIMIT",
    "LOOP_ENGINEERING_RULES",
    "LoopHarness",
    "LoopHooks",
    "LoopRunResult",
    "LoopTurnContext",
    "extract_reply",
    "LoopStepMetrics",
]
