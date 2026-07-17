"""BillMind M12 意图分类器包 — Rule / BERT / Embedding + 默认三级漏斗。"""

from __future__ import annotations

from agent.intent.classifiers.bert import BertClassifier
from agent.intent.classifiers.embedding import EmbeddingClassifier
from agent.intent.classifiers.rule import RuleClassifier
from agent.intent.manager import IntentResult

rule = RuleClassifier()
bert = BertClassifier()
embedding = EmbeddingClassifier()

_PREPARED = False


def init() -> None:
    """预热三级分类器（Rule → BERT → Embedding）。"""
    global _PREPARED
    if _PREPARED:
        return
    rule.prepare()
    bert.prepare()
    embedding.prepare()
    _PREPARED = True


def classify(text: str) -> IntentResult:
    """生产默认漏斗：Rule → BERT → Embedding → fallback_all。"""
    if hit := rule.classify(text):
        return hit
    if hit := bert.classify(text):
        return hit
    if hit := embedding.classify(text):
        return hit
    return IntentResult(
        scene="fallback_all",
        confidence=0.0,
        method="hybrid_fallback",
    )


__all__ = [
    "BertClassifier",
    "EmbeddingClassifier",
    "RuleClassifier",
    "bert",
    "classify",
    "embedding",
    "init",
    "rule",
]
