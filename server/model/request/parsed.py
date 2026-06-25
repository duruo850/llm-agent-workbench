"""LLM 解析结果（无数据库表，M0/M2 输入）。"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field

from common.llm import format_json

REQUIRED_FIELDS = ("amount", "category", "merchant", "note")


@dataclass
class ParsedTransaction:
    """LLM 解析后的记账记录。"""

    amount: float = Field(description="金额，收入为正数，支出也为正数（由 category 区分收支）")
    category: str = Field(description="分类，如「餐饮」「交通」「工资」「购物」等；无法判断时用「其他」")
    merchant: str = Field(description="商户或来源，如 Starbucks、地铁、盒马；无法判断时用空字符串")
    note: str = Field(description="补充说明，没有则用空字符串")


# 向后兼容 M0 示例中的 Transaction 名称
Transaction = ParsedTransaction


def LoadTransaction(data: dict) -> ParsedTransaction:
    """校验 LLM 返回的 JSON 是否包含所需字段且类型正确。"""
    if missing := [f for f in REQUIRED_FIELDS if f not in data]:
        raise ValueError(f"JSON 缺少字段: {missing}")

    data = format_json(data)

    amount = data["amount"]
    if not isinstance(amount, (int, float)):
        raise ValueError(f"amount 应为数字，实际为 {type(amount).__name__}")

    return ParsedTransaction(
        amount=float(amount),
        category=str(data["category"]),
        merchant=str(data["merchant"]),
        note=str(data["note"]) if data["note"] is not None else "",
    )
