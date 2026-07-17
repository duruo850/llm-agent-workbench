"""BertClassifier 单测 — 漏斗顺位与分类行为。"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import agent.intent.classifiers as classifiers
from agent.intent.manager import IntentResult


def test_funnel_bert_second() -> None:
    """Rule 未命中时，由 BERT 承接；不调用 Embedding。"""
    rule = MagicMock()
    bert = MagicMock()
    embedding = MagicMock()
    rule.classify.return_value = None
    bert.classify.return_value = IntentResult(scene="rag_knowledge", confidence=0.85, method="bert")
    with patch.object(classifiers, "rule", rule), patch.object(classifiers, "bert", bert), patch.object(
        classifiers, "embedding", embedding
    ):
        result = classifiers.classify("some query")

    assert result.scene == "rag_knowledge"
    assert result.method == "bert"
    bert.classify.assert_called_once()
    embedding.classify.assert_not_called()
