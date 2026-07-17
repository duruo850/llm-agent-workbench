"""Skill 分类元数据 — 供 SkillRegistry 与意图层 Rule/BERT/Embedding 查询。"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

type SkillCategoryId = Literal[
    "mcp_gaode",
    "rag_knowledge",
    "transaction",
    "general_chat",
    "fallback_all",
]

SkillCategoryMcpGaode: SkillCategoryId = "mcp_gaode"  # 高德地图
SkillCategoryRagKnowledge: SkillCategoryId = "rag_knowledge"  # 知识库
SkillCategoryTransaction: SkillCategoryId = "transaction"  # 交易
SkillCategoryGeneralChat: SkillCategoryId = "general_chat"  # 通用聊天
SkillCategoryFallbackAll: SkillCategoryId = "fallback_all"  # 兜底分类

# 可注册的 4 个具体 skill 分类（不含 fallback_all）
SKILL_CATEGORY_IDS: tuple[SkillCategoryId, ...] = (
    SkillCategoryMcpGaode,
    SkillCategoryRagKnowledge,
    SkillCategoryTransaction,
    SkillCategoryGeneralChat,
)

FALLBACK_ALL_DESCRIPTION = "未命中任何分类或置信度过低时回退到全量工具"


@dataclass(frozen=True)
class SkillCategoryDef:
    """单个 skill 分类的语义；tool_names 由 SkillRegistry 运行时填充。"""

    id: SkillCategoryId
    description: str
    keywords: tuple[str, ...]
    patterns: tuple[str, ...]
    tool_names: tuple[str, ...] = ()

    def with_tool_names(self, tool_names: tuple[str, ...]) -> SkillCategoryDef:
        """附加运行时 tool 名，返回新实例（frozen dataclass）。"""
        return replace(self, tool_names=tool_names)

    @classmethod
    def lookup(cls, category_id: str) -> SkillCategoryDef | None:
        """按 category_id 查找静态定义（不含运行时 tool_names）。"""
        if category_id == "fallback_all":
            return cls(
                id="fallback_all",
                description=FALLBACK_ALL_DESCRIPTION,
                keywords=(),
                patterns=(),
            )
        return SKILL_CATEGORY_DEFS.get(category_id)


# 分类定义
SKILL_CATEGORY_DEFS: dict[str, SkillCategoryDef] = {}


def register_skill_category(
    category_id: SkillCategoryId,
    *,
    description: str,
    keywords: tuple[str, ...] = (),
    patterns: tuple[str, ...] = (),
) -> None:
    """在 skill / MCP 模块顶层调用一次；重复注册以首次为准。"""
    if category_id in SKILL_CATEGORY_DEFS:
        return
    if category_id == "fallback_all":
        return
    SKILL_CATEGORY_DEFS[category_id] = SkillCategoryDef(
        id=category_id,
        description=description,
        keywords=keywords,
        patterns=patterns,
    )
