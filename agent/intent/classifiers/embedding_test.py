"""EmbeddingClassifier 单测 — 漏斗顺位与分类行为。"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import agent.intent.classifiers as classifiers
from agent.intent.manager import IntentResult


def test_funnel_embedding_third() -> None:
    """Rule、BERT 均未命中时，由 Embedding 承接。"""
    rule = MagicMock()
    bert = MagicMock()
    embedding = MagicMock()
    rule.classify.return_value = None
    bert.classify.return_value = None
    embedding.classify.return_value = IntentResult(
        scene="transaction", confidence=0.75, method="embedding"
    )
    with patch.object(classifiers, "rule", rule), patch.object(classifiers, "bert", bert), patch.object(
        classifiers, "embedding", embedding
    ):
        result = classifiers.classify("ambiguous")

    assert result.scene == "transaction"
    assert result.method == "embedding"
    embedding.classify.assert_called_once()
