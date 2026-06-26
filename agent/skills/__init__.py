"""Agent skills — 按领域拆分 @tool，统一合并为对外工具列表。"""

from __future__ import annotations

import importlib
import pkgutil

from langchain_core.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

import agent.skills as _skills_pkg
from agent.promt.policy import ToolPromptPolicy

SKILL_TOOLS: dict[str, BaseTool] = {}
SKILL_TOOLS_MAP: dict[str, BaseTool] = {}
SKILL_POLICYS: dict[str, ToolPromptPolicy] = {}


def discover_skill_modules(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """扫描 ``agent/skills/`` 子模块，首次调用时填充 SKILL_TOOLS / SKILL_TOOLS_MAP / SKILL_POLICYS。"""
    if SKILL_TOOLS:
        return

    prefix = f"{_skills_pkg.__name__}."
    for module_info in pkgutil.iter_modules(_skills_pkg.__path__, prefix):
        short_name = module_info.name.removeprefix(prefix)
        if short_name.startswith("_"):
            continue
        module = importlib.import_module(module_info.name)
        policies = getattr(module, "POLICIES", None)
        if isinstance(policies, dict):
            SKILL_POLICYS.update(policies)
        builders = getattr(module, "TOOL_BUILDERS", None)
        if isinstance(builders, list):
            for build in builders:
                tool_obj = build(session_factory)
                SKILL_TOOLS[tool_obj.name] = tool_obj
                SKILL_TOOLS_MAP[tool_obj.name] = tool_obj


__all__ = ["SKILL_TOOLS", "SKILL_TOOLS_MAP", "SKILL_POLICYS", "discover_skill_modules"]
