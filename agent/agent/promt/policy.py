"""工具 prompt 编排元数据 — 供 promt.system_prompt 自动生成规则。"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, Literal

from langchain_core.tools import BaseTool, tool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

SessionFactory = async_sessionmaker[AsyncSession]

OUT_OF_SCOPE_REPLY = "抱歉，BillMind 仅支持账单记账与查询相关业务。"

SkillToolFn = Callable[..., Awaitable[str]]


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


def _skill_module_globals() -> dict[str, Any]:
    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        raise RuntimeError("tool_policy 无法定位所属 skill 模块")
    current = frame.f_back
    while current is not None:
        name = current.f_globals.get("__name__", "")
        if name.startswith("agent.agent.skills.") and not name.endswith(".__init__"):
            return current.f_globals
        current = current.f_back
    raise RuntimeError("tool_policy 无法定位 agent.skills 模块")


def _register_skill_tool(fn: SkillToolFn, policy: ToolPromptPolicy) -> SkillToolFn:
    params = list(inspect.signature(fn).parameters)
    if not params or params[0] != "db":
        raise TypeError(f"{fn.__name__} 首个参数必须是 db: AsyncSession")

    module_globals = _skill_module_globals()
    policies: dict[str, ToolPromptPolicy] = module_globals.setdefault("POLICIES", {})
    builders: list[Callable[[SessionFactory], BaseTool]] = module_globals.setdefault(
        "TOOL_BUILDERS", []
    )

    policies[fn.__name__] = policy

    def build(session_factory: SessionFactory) -> BaseTool:
        sig = inspect.signature(fn)
        llm_sig = sig.replace(parameters=[p for n, p in sig.parameters.items() if n != "db"])

        @wraps(fn)
        async def llm_tool(*args: Any, **kwargs: Any) -> str:
            async with session_factory() as db:
                return await fn(db, *args, **kwargs)

        llm_tool.__signature__ = llm_sig
        return tool(llm_tool)

    builders.append(build)
    return fn


def tool_policy(
    *,
    scope: str,
    time_scope: Literal["day", "month", "none"] = "none",
    user_triggers: tuple[str, ...] = (),
    month_triggers: tuple[str, ...] = ("本月", "这个月"),
    time_param: str = "",
    forbid_tools: tuple[str, ...] = (),
    example_queries: tuple[str, ...] = (),
    example_note: str = "",
) -> Callable[[SkillToolFn], SkillToolFn]:
    """装饰 skill 实现函数：首参为 ``db``，``Agent.init`` 时绑定为 LangChain @tool。"""
    policy = ToolPromptPolicy(
        scope=scope,
        time_scope=time_scope,
        user_triggers=user_triggers,
        month_triggers=month_triggers,
        time_param=time_param,
        forbid_tools=forbid_tools,
        example_queries=example_queries,
        example_note=example_note,
    )

    def decorator(fn: SkillToolFn) -> SkillToolFn:
        return _register_skill_tool(fn, policy)

    return decorator
