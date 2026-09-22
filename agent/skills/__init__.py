"""Agent skills — 按领域拆分 @tool，统一由 SkillRegistry 聚合。"""

from __future__ import annotations

import importlib
import pkgutil

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agent.common.skill_registry import skill_registry

_INITIALIZED = False


def _import_skill_modules(module_name: str) -> None:
    """import skill 模块，触发 ``@tool_register`` 注册到 SkillRegistry。"""
    short_name = module_name.rsplit(".", 1)[-1]
    if short_name.endswith("_test") or short_name.startswith("test_"):
        return

    module = importlib.import_module(module_name)
    if not hasattr(module, "__path__"):
        return

    prefix = f"{module_name}."
    for sub_info in pkgutil.iter_modules(module.__path__, prefix):
        short = sub_info.name.removeprefix(prefix).split(".")[-1]
        if short.startswith("_") or short == "route":
            continue
        if short.endswith("_test") or short.startswith("test_"):
            continue
        _import_skill_modules(sub_info.name)


def init(db_session_factory: async_sessionmaker[AsyncSession]) -> None:
    """扫描 ``agent/skills/`` 及子包（如 ``file/``），注册到 SkillRegistry。"""
    global _INITIALIZED
    if _INITIALIZED:
        return

    prefix = f"{__name__}."
    for module_info in pkgutil.iter_modules(__path__, prefix):
        short_name = module_info.name.removeprefix(prefix)
        if short_name.startswith("_"):
            continue
        _import_skill_modules(module_info.name)

    skill_registry.init(db_session_factory)
    _INITIALIZED = True


__all__ = ["init"]
