"""Agent skills — 按领域拆分 @tool，统一合并为对外工具列表。"""

from __future__ import annotations

import importlib
import pkgutil

from langchain_core.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agent.agent.promt.policy import ToolPromptPolicy

SKILL_TOOLS: dict[str, BaseTool] = {}
SKILL_TOOLS_MAP: dict[str, BaseTool] = {}
SKILL_POLICYS: dict[str, ToolPromptPolicy] = {}


def _register_module_tools(
    module_name: str,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    module = importlib.import_module(module_name)
    policies = getattr(module, "POLICIES", None)
    if isinstance(policies, dict):
        SKILL_POLICYS.update(policies)
    builders = getattr(module, "TOOL_BUILDERS", None)
    if isinstance(builders, list):
        for build in builders:
            tool_obj = build(db_session_factory)
            SKILL_TOOLS[tool_obj.name] = tool_obj
            SKILL_TOOLS_MAP[tool_obj.name] = tool_obj

    if not hasattr(module, "__path__"):
        return

    prefix = f"{module_name}."
    for sub_info in pkgutil.iter_modules(module.__path__, prefix):
        short = sub_info.name.removeprefix(prefix).split(".")[-1]
        if short.startswith("_") or short == "route":
            continue
        _register_module_tools(sub_info.name, db_session_factory)


def init(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    """扫描 ``agent/skills/`` 及子包（如 ``file/``），填充 SKILL_TOOLS。"""
    if SKILL_TOOLS:
        return

    prefix = f"{__name__}."
    for module_info in pkgutil.iter_modules(__path__, prefix):
        short_name = module_info.name.removeprefix(prefix)
        if short_name.startswith("_"):
            continue
        _register_module_tools(module_info.name, db_session_factory)


__all__ = ["SKILL_TOOLS", "SKILL_TOOLS_MAP", "SKILL_POLICYS", "discover_skill_modules"]
