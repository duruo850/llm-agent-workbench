"""方案 1 — RuleClassifier: 关键词 + 正则完整匹配分类。"""

from __future__ import annotations

import re

from agent.common.skill_registry import skill_registry
from agent.intent.manager import IntentResult

_CJK_BOUNDARY = r"[，。！？、\s,.!?;:]"


def _keyword_full_match(text: str, keyword: str) -> bool:
    """整句相等或词边界短语匹配（弃用偶然子串命中）。"""
    if not keyword:
        return False
    normalized = text.strip()
    kw = keyword.strip()
    if not normalized or not kw:
        return False
    if normalized == kw or normalized.lower() == kw.lower():
        return True
    escaped = re.escape(kw)
    if re.search(rf"^{escaped}(?:{_CJK_BOUNDARY}|$)", normalized, re.IGNORECASE):
        return True
    if re.search(rf"(?:{_CJK_BOUNDARY}|^){escaped}(?:{_CJK_BOUNDARY}|$)", normalized, re.IGNORECASE):
        return True
    if re.search(rf"{escaped}$", normalized, re.IGNORECASE):
        return True
    if len(kw) >= 2 and kw in normalized:
        return True
    return False


class RuleClassifier:
    """命中关键词或正则即 confidence=1.0；四类统一完整匹配。"""

    def __init__(self) -> None:
        self._compiled: dict[str, list[re.Pattern[str]]] = {}
        self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    def prepare(self) -> bool:
        """读 SkillRegistry + 编译正则。"""
        self._compiled.clear()
        for category_id in skill_registry.all_categories():
            defn = skill_registry.get_category_def(category_id)
            self._compiled[category_id] = [
                re.compile(p, re.IGNORECASE) for p in defn.patterns
            ]
        self._ready = True
        return True

    def refresh(self) -> None:
        """向后兼容别名。"""
        self.prepare()

    def classify(self, text: str) -> IntentResult | None:
        if not self._ready:
            self.prepare()
        normalized = text.strip()
        if not normalized:
            return None

        for category_id in skill_registry.all_categories():
            defn = skill_registry.get_category_def(category_id)
            if any(_keyword_full_match(normalized, kw) for kw in defn.keywords):
                return IntentResult(scene=category_id, confidence=1.0, method="rule")
            for pattern in self._compiled.get(category_id, []):
                if pattern.fullmatch(normalized):
                    return IntentResult(scene=category_id, confidence=1.0, method="rule")

        return None
