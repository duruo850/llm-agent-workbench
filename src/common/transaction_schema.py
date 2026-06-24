"""记账解析共享 Schema：ParsedTransaction 与 JSON 校验。"""

from __future__ import annotations

import json
from dataclasses import dataclass

from pydantic import Field

REQUIRED_FIELDS = ("amount", "category", "merchant", "note")


@dataclass
class ParsedTransaction:
    """LLM 解析后的记账记录。"""

    amount: float = Field(description="金额，收入为正数，支出也为正数（由 category 区分收支）")
    category: str = Field(description="分类，如「餐饮」「交通」「工资」「购物」等；无法判断时用「其他」")
    merchant: str = Field(description="商户或来源，如 Starbucks、地铁、盒马；无法判断时用空字符串")
    note: str = Field(description="补充说明，没有则用空字符串")


def parse_llm_json(raw_output: str) -> dict:
    """清理 markdown 代码块并解析 LLM 输出的 JSON 字符串。"""
    cleaned = raw_output.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 解析失败，原始输出：\n{raw_output}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"期望 JSON 对象，实际为 {type(data).__name__}")

    return data


def validate_fields(data: dict) -> ParsedTransaction:
    """校验 LLM 返回的 JSON 是否包含所需字段且类型正确。"""
    if missing := [f for f in REQUIRED_FIELDS if f not in data]:
        raise ValueError(f"JSON 缺少字段: {missing}")

    amount = data["amount"]
    if not isinstance(amount, (int, float)):
        raise ValueError(f"amount 应为数字，实际为 {type(amount).__name__}")

    return ParsedTransaction(
        amount=float(amount),
        category=str(data["category"]),
        merchant=str(data["merchant"]),
        note=str(data["note"]) if data["note"] is not None else "",
    )
