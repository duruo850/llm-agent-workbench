"""统一 Skill 注册表 — 聚合 category 元数据、local tools 与 MCP tools。"""

from __future__ import annotations

import logging
from collections import defaultdict

from langchain_core.tools import BaseTool

from agent.common.skill_category import (
    SKILL_CATEGORY_IDS,
    SkillCategoryDef,
    SkillCategoryId,
)
from agent.common.skill_policy import SessionFactory, ToolPromptPolicy

logger = logging.getLogger("billmind.skill_registry")


class SkillRegistry:
    """Skill 分类与 tools 的单例注册表。"""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}  # 工具字典
        self._policies: dict[str, ToolPromptPolicy] = {}  # 策略字典
        self._category_tools: dict[str, list[BaseTool]] = defaultdict(list)  # 分类工具字典
        self._db_factory: SessionFactory | None = None  # 数据库会话工厂

    def register_policy(self, tool_name: str, policy: ToolPromptPolicy) -> None:
        """登记 tool 的 prompt policy（由 ``tool_register`` 装饰器调用）。"""
        self._policies[tool_name] = policy

    def register_skills(
        self,
        tools: list[BaseTool],
        *,
        category_id: SkillCategoryId | None = None,
    ) -> None:
        """注册一批 BaseTool；无 policy 的 tool（如 MCP）须传 ``category_id``。"""
        for tool_obj in tools:
            self._register_tool(tool_obj, category_id=category_id)

    def init(self, db_session_factory: SessionFactory) -> None:
        """注入 db 会话工厂；须在 skill 模块 import 之后调用。"""
        self._db_factory = db_session_factory

    def all_categories(self) -> tuple[SkillCategoryId, ...]:
        """获取所有已注册的 skill 分类 ID。"""
        return SKILL_CATEGORY_IDS  # type: ignore[return-value]

    def get_category_def(self, category_id: SkillCategoryId) -> SkillCategoryDef:
        """获取某分类的完整元数据（description / keywords / patterns / tool_names）。"""
        base = SkillCategoryDef.lookup(category_id)
        if base is None:
            raise KeyError(f"unknown skill category: {category_id}")
        return base.with_tool_names(self.category_tool_names(category_id))

    def category_tool_names(self, category_id: SkillCategoryId) -> tuple[str, ...]:
        """获取某分类下的 tool 名列表。"""
        return tuple(t.name for t in self._category_tools.get(category_id, ()))

    def tools_for_category(self, category_id: SkillCategoryId) -> list[BaseTool]:
        """获取某个分类的全部 skills（BaseTool 实例）。"""
        return list(self._category_tools.get(category_id, ()))

    def all_tool_names(self) -> tuple[str, ...]:
        """获取所有已注册 tool 名（local + MCP）。"""
        return tuple(sorted(self._tools))

    def all_tools(self) -> list[BaseTool]:
        """获取所有 skills（全部 BaseTool 实例）。"""
        return list(self._tools.values())

    def get_tool(self, name: str) -> BaseTool | None:
        """按名获取单个 skill。"""
        return self._tools.get(name)

    def tools_map(self) -> dict[str, BaseTool]:
        """获取 name → BaseTool 只读映射。"""
        return dict(self._tools)

    def all_policies(self) -> dict[str, ToolPromptPolicy]:
        """获取所有 tool 的 prompt policy。"""
        return dict(self._policies)

    def policy_for_tool(self, name: str) -> ToolPromptPolicy | None:
        """获取单个 tool 的 policy。"""
        return self._policies.get(name)

    def _register_tool(
        self,
        tool_obj: BaseTool,
        *,
        category_id: SkillCategoryId | None,
    ) -> None:
        name = tool_obj.name
        self._tools[name] = tool_obj
        cat = category_id
        if cat is None:
            policy = self._policies.get(name)
            if policy is None:
                raise ValueError(f"tool {name!r} 无 policy 且未指定 category_id")
            cat = policy.skill_category
        if not any(t.name == name for t in self._category_tools[cat]):
            self._category_tools[cat].append(tool_obj)


skill_registry = SkillRegistry()
