"""scorers 单元测试 — 验证打分逻辑，不跑完整 Eval。

与 ``run_eval.py`` 的区别
-------------------------
- 这里：**不调** ``Agent.invoke``、**不调** LLM、**不连** PostgreSQL
- 传入伪造的 ``actual_tools`` / ``reply`` 字符串，断言 ``score_tools`` 等函数的 ``passed`` / ``score``

快速运行::

    .venv/bin/python3.14 -m pytest utils/agent/eval/scorers_test.py -v
"""

from __future__ import annotations

import pytest

from utils.agent.eval.scorers import (
    aggregate_scores,
    score_reply_keywords,
    score_tools,
)


@pytest.mark.parametrize(
    ("actual", "expected", "match", "passed"),
    [
        (["add_transaction"], ["add_transaction"], "all", True),
        (["query_transactions"], ["add_transaction"], "all", False),
        (["get_monthly_summary"], ["add_transaction", "get_monthly_summary"], "any", True),
        ([], [], "all", True),
        ([], [], "none", True),
        (["add_transaction"], [], "none", False),
        (
            ["add_transaction", "query_transactions"],
            ["add_transaction", "query_transactions"],
            "sequence",
            True,
        ),
        (
            ["query_transactions", "add_transaction"],
            ["add_transaction", "query_transactions"],
            "sequence",
            False,
        ),
    ],
)
def test_score_tools(
    actual: list[str],
    expected: list[str],
    match: str,
    passed: bool,
) -> None:
    result = score_tools(actual, expected, match=match)  # type: ignore[arg-type]
    assert result.passed is passed
    assert 0.0 <= result.score <= 1.0


def test_score_tools_forbidden() -> None:
    result = score_tools(
        ["add_transaction", "query_transactions"],
        ["add_transaction"],
        forbidden_tools=["query_transactions"],
    )
    assert result.passed is False
    assert result.score == 0.0


@pytest.mark.parametrize(
    ("reply", "keywords", "passed", "score"),
    [
        ("本月餐饮共花费 120 元", ["餐饮", "120"], True, 1.0),
        ("本月交通花费 50 元", ["餐饮", "120"], False, 0.0),
    ],
)
def test_score_reply_keywords_all_required(
    reply: str,
    keywords: list[str],
    passed: bool,
    score: float,
) -> None:
    result = score_reply_keywords(reply, keywords)
    assert result.passed is passed
    assert result.score == score


def test_score_reply_keywords_any() -> None:
    result = score_reply_keywords("好的，已记录", ["记录", "失败"], match_all=False)
    assert result.passed is True


def test_aggregate_scores() -> None:
    child_a = score_tools(["add_transaction"], ["add_transaction"])
    child_b = score_reply_keywords("已帮你记一笔", ["记"])
    agg = aggregate_scores([child_a, child_b])
    assert agg.passed is True
    assert agg.score == pytest.approx(1.0)

    agg_fail = aggregate_scores([child_a, score_reply_keywords("好的", ["不存在"])])
    assert agg_fail.passed is False
