"""工具 prompt 编排元数据 — 供 runner._system_prompt 自动生成规则。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OUT_OF_SCOPE_REPLY = "抱歉，BillMind 仅支持账单记账与查询相关业务。"


@dataclass(frozen=True)
class ToolPromptPolicy:
    """单个 @tool 在 system prompt 中的编排说明（与 docstring 互补）。"""

    scope: str
    time_scope: Literal["day", "month", "none"] = "none"
    user_triggers: tuple[str, ...] = ()
    month_triggers: tuple[str, ...] = ("本月", "这个月")
    time_param: str = ""
    forbid_tools: tuple[str, ...] = ()
    example_queries: tuple[str, ...] = ()
    example_note: str = ""
