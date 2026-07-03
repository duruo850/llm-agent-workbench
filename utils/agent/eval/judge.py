"""LLM-as-judge — 独立于 Agent 主对话的回复质量评审。"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class JudgeResult:
    passed: bool
    score: float
    detail: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


async def judge_reply(
    reply: str,
    criteria: str,
    *,
    llm: Any | None = None,
) -> JudgeResult:
    """用 LLM 评审助手回复，返回 ``{passed, score, reason}`` 结构化结果。"""
    criteria_text = criteria.strip()
    if not criteria_text:
        return JudgeResult(
            passed=True,
            score=1.0,
            detail="no criteria configured",
        )

    if llm is None:
        from common.llm import get_openai_chat_llm

        llm = get_openai_chat_llm()

    prompt = (
        "你是 BillMind Agent 回复质量评审员。\n"
        f"评审标准：{criteria_text}\n\n"
        f"助手回复：{reply}\n\n"
        "仅输出 JSON：{\"passed\": bool, \"score\": 0~1 浮点, \"reason\": \"简短理由\"}"
    )
    response = await llm.ainvoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)
    try:
        payload = json.loads(str(content).strip())
    except json.JSONDecodeError:
        return JudgeResult(
            passed=False,
            score=0.0,
            detail=f"invalid judge JSON: {content!r}",
        )

    passed = bool(payload.get("passed"))
    raw_score = payload.get("score", 0.0)
    try:
        score = max(0.0, min(1.0, float(raw_score)))
    except (TypeError, ValueError):
        score = 1.0 if passed else 0.0

    return JudgeResult(
        passed=passed,
        score=score,
        detail=str(payload.get("reason", "")),
        meta={"criteria": criteria_text, "raw": payload},
    )
