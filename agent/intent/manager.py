"""M12 IntentManager — 类型定义、分类器生命周期、查询与 tools 解析。"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Literal

from langchain_core.tools import BaseTool

from agent.common.skill_category import SKILL_CATEGORY_IDS, SkillCategoryId

logger = logging.getLogger("billmind.intent.manager")

IntentMethod = Literal["rule", "embedding", "bert", "hybrid_fallback"]
ClassifierMethod = Literal["rule", "embedding", "bert", "hybrid"]

CATEGORY_TO_LABEL: dict[str, int] = {
    category_id: idx for idx, category_id in enumerate(SKILL_CATEGORY_IDS)
}
LABEL_TO_CATEGORY: dict[int, str] = {v: k for k, v in CATEGORY_TO_LABEL.items()}


@dataclass(frozen=True)
class IntentCandidate:
    """分类候选（Embedding / BERT Top-K）。"""

    scene: str
    confidence: float


@dataclass(frozen=True)
class IntentResult:
    """意图分类结果 — scene 为 skill category_id 或 fallback_all。"""

    scene: str
    confidence: float
    method: IntentMethod | str
    candidates: tuple[IntentCandidate, ...] = field(default_factory=tuple)

    @property
    def is_fallback(self) -> bool:
        return self.scene == "fallback_all" or self.method == "hybrid_fallback"


_FALLBACK = IntentResult(scene="fallback_all", confidence=0.0, method="hybrid_fallback")

# 类型定义完毕后再导入 classifiers，避免循环依赖。
from agent.intent.classifiers import bert, classify, embedding, init, rule  # noqa: E402


class IntentManager:
    """意图层入口 — prepare / classify / resolve_tools。"""

    def init(self) -> None:
        """启动预处理（一次）：Rule → BERT → Embedding 三级漏斗。"""
        logger.info("IntentManager.prepare hybrid funnel (rule → bert → embedding)")
        init()

    def classify(
        self,
        text: str,
        *,
        method: ClassifierMethod | None = None,
    ) -> IntentResult:
        """默认走三级漏斗；显式 ``method`` 仅用于调试 / 评测单路分类器。"""
        if method is None or method == "hybrid":
            return classify(text)
        if method == "rule":
            return rule.classify(text) or _FALLBACK
        if method == "embedding":
            return embedding.classify(text) or _FALLBACK
        if method == "bert":
            return bert.classify(text) or _FALLBACK

    def resolve_tools(self, category_id: SkillCategoryId) -> list[BaseTool]:
        """命中后从 SkillRegistry 取该分类全部 skills。"""
        from agent.common.skill_registry import skill_registry

        if category_id == "fallback_all":
            return skill_registry.all_tools()
        return skill_registry.tools_for_category(category_id)


intent_manager = IntentManager()
