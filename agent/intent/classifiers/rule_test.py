"""RuleClassifier 单测。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

from agent.intent.classifiers.rule import RuleClassifier
from agent.skills import init as init_skills
from common.env import get_database_url
from server.db.session import Database


def _fresh_classifier() -> RuleClassifier:
    Database.init(get_database_url())
    init_skills(Database.get().async_session_factory)
    clf = RuleClassifier()
    clf.prepare()
    return clf


def test_rule_transaction_write() -> None:
    clf = _fresh_classifier()
    result = clf.classify("刚才 Starbucks 花了 38，算餐饮")
    assert result is not None
    assert result.scene == "transaction"
    assert result.confidence == 1.0
    assert result.method == "rule"


def test_rule_transaction_query() -> None:
    clf = _fresh_classifier()
    result = clf.classify("查一下本月餐饮花了多少")
    assert result is not None
    assert result.scene == "transaction"


def test_rule_rag_knowledge() -> None:
    clf = _fresh_classifier()
    result = clf.classify("基金定投有什么好处")
    assert result is not None
    assert result.scene == "rag_knowledge"


def test_rule_general_chat() -> None:
    clf = _fresh_classifier()
    result = clf.classify("你好，你能做什么")
    assert result is not None
    assert result.scene == "general_chat"


def test_rule_no_match() -> None:
    clf = _fresh_classifier()
    assert clf.classify("xyz abc 随机文本无关键词") is None


def test_funnel_rule_first() -> None:
    """Rule 命中时，漏斗不调用 BERT / Embedding。"""
    from unittest.mock import MagicMock, patch

    import agent.intent.classifiers as classifiers
    from agent.intent.manager import IntentResult

    rule = MagicMock()
    bert = MagicMock()
    embedding = MagicMock()
    rule.classify.return_value = IntentResult(scene="transaction", confidence=1.0, method="rule")
    with patch.object(classifiers, "rule", rule), patch.object(classifiers, "bert", bert), patch.object(
        classifiers, "embedding", embedding
    ):
        result = classifiers.classify("花了 10 元")

    assert result.scene == "transaction"
    assert result.method == "rule"
    rule.classify.assert_called_once()
    bert.classify.assert_not_called()
    embedding.classify.assert_not_called()
