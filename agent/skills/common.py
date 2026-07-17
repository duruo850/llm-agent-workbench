"""Skill 注册装饰器 — 包装 async skill 函数为 BaseTool 并写入 SkillRegistry。"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, Literal, TypeVar

from langchain_core.tools import tool

from agent.common.skill_category import SkillCategoryId
from agent.common.skill_policy import ToolPromptPolicy
from agent.common.skill_registry import skill_registry


# 注入的参数
_INJECTED_PARAMS = frozenset({"db", "config"})

# 函数类型  
_F = TypeVar("_F", bound=Callable[..., Awaitable[str]])


def _validate_skill_fn(fn: Callable[..., Awaitable[str]]) -> None:
    """验证 skill 函数是否符合要求。"""
    sig = inspect.signature(fn)
    params = list(sig.parameters)
    if not params or params[0] != "db":
        raise TypeError(f"{fn.__name__} 首参必须是 db: AsyncSession")
    if "config" not in sig.parameters:
        raise TypeError(f"{fn.__name__} 须包含 config: RunnableConfig 参数")


def tool_register(
    *,
    scope: str,
    skill_category: SkillCategoryId,
    time_scope: Literal["day", "month", "none"] = "none",
    user_triggers: tuple[str, ...] = (),
    month_triggers: tuple[str, ...] = ("本月", "这个月"),
    time_param: str = "",
    forbid_tools: tuple[str, ...] = (),
    example_queries: tuple[str, ...] = (),
    example_note: str = "",
) -> Callable[[_F], _F]:
    """装饰 skill 函数：包装为 BaseTool 并 ``register_skills``，模块内仍保留原 async def。"""
    policy = ToolPromptPolicy(
        scope=scope,
        skill_category=skill_category,
        time_scope=time_scope,
        user_triggers=user_triggers,
        month_triggers=month_triggers,
        time_param=time_param,
        forbid_tools=forbid_tools,
        example_queries=example_queries,
        example_note=example_note,
    )

    def decorator(fn: _F) -> _F:
        _validate_skill_fn(fn)
        skill_registry.register_policy(fn.__name__, policy)

        sig = inspect.signature(fn)
        llm_sig = sig.replace(
            parameters=[p for n, p in sig.parameters.items() if n not in _INJECTED_PARAMS]
        )
        registry = skill_registry

        @wraps(fn)
        async def llm_tool(*args: Any, **kwargs: Any) -> str:
            if registry._db_factory is None:
                raise RuntimeError("SkillRegistry 未 init，请先调用 agent.skills.init()")
            async with registry._db_factory() as db:
                return await fn(db, *args, **kwargs)

        llm_tool.__signature__ = llm_sig
        skill_registry.register_skills([tool(llm_tool)])
        return fn

    return decorator
