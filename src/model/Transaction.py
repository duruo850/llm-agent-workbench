"""记账领域模型与字段校验。"""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field
from src.common.llm import format_json

REQUIRED_FIELDS = ("amount", "category", "merchant", "note")


@dataclass
class Transaction:
    """LLM 解析后的记账记录。"""

    amount: float = Field(description="金额，收入为正数，支出也为正数（由 category 区分收支）")
    category: str = Field(description="分类，如「餐饮」「交通」「工资」「购物」等；无法判断时用「其他」")
    merchant: str = Field(description="商户或来源，如 Starbucks、地铁、盒马；无法判断时用空字符串")
    note: str = Field(description="补充说明，没有则用空字符串")


def LoadTransaction(data: dict) -> Transaction:
    """校验 LLM 返回的 JSON 是否包含所需字段且类型正确。

    Args:
        data: ``format_json`` 的返回值。示例：
            ``{"amount": 38.0, "category": "餐饮", "merchant": "Starbucks", "note": ""}``

    Returns:
        校验通过的 ``Transaction``。示例：
            ``Transaction(amount=38.0, category="餐饮", merchant="Starbucks", note="")``
    """
    if missing := [f for f in REQUIRED_FIELDS if f not in data]:
        raise ValueError(f"JSON 缺少字段: {missing}")
    
    # 清理 markdown 代码块并解析 LLM 输出的 JSON 字符串。
    data = format_json(data)

    amount = data["amount"]
    if not isinstance(amount, (int, float)):
        raise ValueError(f"amount 应为数字，实际为 {type(amount).__name__}")

    return Transaction(
        amount=float(amount),
        category=str(data["category"]),
        merchant=str(data["merchant"]),
        note=str(data["note"]) if data["note"] is not None else "",
    )
