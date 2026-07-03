"""Eval 打分器 — 工具选择与回复质量。

本模块只做**判定逻辑**，不启动 Agent、不访问数据库、不调用 HTTP。
``run_eval.py`` 在拿到 ``Agent.invoke`` 的回复与实际工具链后，调用这里的函数打分；
``scorers_test.py`` 用伪造的 ``actual_tools`` / ``reply`` 验证判定是否正确。

打分维度
--------
1. ``score_tools`` — 实际调用的 skill 名 vs ``test_cases.json`` 里的 ``expected_tools``
2. ``score_reply_keywords`` — 助手回复是否包含期望关键词（大小写 / 空白不敏感）
3. ``score_llm_judge`` — 可选；委托 ``utils.agent.eval.judge``（``--llm-judge`` 时启用）
4. ``aggregate_scores`` — 子项全部 ``passed`` 才算通过，``score`` 取算术平均
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

from utils.agent.eval.judge import judge_reply

ToolMatchMode = Literal["all", "any", "sequence", "none"]


@dataclass
class ScoreResult:
    """单项打分结果 — ``run_eval.py`` 打印 ``name`` / ``passed`` / ``score`` / ``detail``。"""

    name: str
    passed: bool
    score: float
    detail: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text.lower())


def score_tools(
    actual_tools: list[str],
    expected_tools: list[str] | None = None,
    *,
    match: ToolMatchMode = "all",
    forbidden_tools: list[str] | None = None,
) -> ScoreResult:
    """比较实际工具链与期望工具集合。

    ``tool_match`` 语义（见 ``test_cases.json`` → ``fields.tool_match``）：

    - ``all`` — 期望工具都出现过即可（顺序无关）
    - ``any`` — 至少命中一个期望工具
    - ``sequence`` — 实际顺序须与 ``expected_tools`` 一致
    - ``none`` — 不应调用任何工具（如纯寒暄）
    """
    actual = [name for name in actual_tools if name]
    expected = list(expected_tools or [])
    forbidden = list(forbidden_tools or [])

    if match == "none":
        passed = not actual
        return ScoreResult(
            name="tools",
            passed=passed,
            score=1.0 if passed else 0.0,
            detail=f"actual={actual}, expected no tools",
            meta={"actual_tools": actual, "expected_tools": expected, "match": match},
        )

    if forbidden and (hits := [name for name in forbidden if name in actual]):
        return ScoreResult(
            name="tools",
            passed=False,
            score=0.0,
            detail=f"forbidden tools called: {hits}",
            meta={"actual_tools": actual, "forbidden_tools": forbidden},
        )

    if not expected:
        passed = True
        score = 1.0
        detail = f"actual={actual}, no expectation"
    elif match == "all":
        missing = [name for name in expected if name not in actual]
        passed = not missing
        score = (len(expected) - len(missing)) / len(expected) if expected else 1.0
        detail = f"actual={actual}, missing={missing}" if missing else f"actual={actual}"
    elif match == "any":
        hits = [name for name in expected if name in actual]
        passed = bool(hits)
        score = 1.0 if passed else 0.0
        detail = f"actual={actual}, hits={hits}"
    elif match == "sequence":
        idx = 0
        for name in actual:
            if idx < len(expected) and name == expected[idx]:
                idx += 1
        passed = idx == len(expected)
        score = idx / len(expected) if expected else 1.0
        detail = f"actual={actual}, expected sequence={expected}, matched={idx}"
    else:
        raise ValueError(f"unsupported tool match mode: {match}")

    return ScoreResult(
        name="tools",
        passed=passed,
        score=score,
        detail=detail,
        meta={"actual_tools": actual, "expected_tools": expected, "match": match},
    )


def score_reply_keywords(
    reply: str,
    keywords: list[str] | None = None,
    *,
    match_all: bool = True,
) -> ScoreResult:
    """关键词命中 — 默认要求全部出现（大小写 / 空白不敏感）。"""
    words = [word.strip() for word in (keywords or []) if word.strip()]
    if not words:
        return ScoreResult(
            name="reply_keywords",
            passed=True,
            score=1.0,
            detail="no keywords configured",
        )

    normalized_reply = _normalize_text(reply)
    hits = [word for word in words if _normalize_text(word) in normalized_reply]
    if match_all:
        passed = len(hits) == len(words)
        score = len(hits) / len(words)
        missing = [word for word in words if word not in hits]
        detail = f"hits={hits}, missing={missing}" if missing else f"hits={hits}"
    else:
        passed = bool(hits)
        score = 1.0 if passed else 0.0
        detail = f"hits={hits}"

    return ScoreResult(
        name="reply_keywords",
        passed=passed,
        score=score,
        detail=detail,
        meta={"keywords": words, "hits": hits},
    )


async def score_llm_judge(
    reply: str,
    criteria: str,
    *,
    llm: Any | None = None,
) -> ScoreResult:
    """Eval 适配层 — 包装 ``utils.agent.eval.judge.judge_reply`` 为 ``ScoreResult``。"""
    result = await judge_reply(reply, criteria, llm=llm)
    return ScoreResult(
        name="llm_judge",
        passed=result.passed,
        score=result.score,
        detail=result.detail,
        meta=result.meta,
    )


def aggregate_scores(results: list[ScoreResult]) -> ScoreResult:
    """合并多个子分数 — 全部通过才算通过，score 取算术平均。"""
    if not results:
        return ScoreResult(name="aggregate", passed=True, score=1.0, detail="no scorers")
    passed = all(item.passed for item in results)
    score = sum(item.score for item in results) / len(results)
    detail = "; ".join(f"{item.name}={'ok' if item.passed else 'fail'}" for item in results)
    return ScoreResult(
        name="aggregate",
        passed=passed,
        score=score,
        detail=detail,
        meta={"children": [item.name for item in results]},
    )
