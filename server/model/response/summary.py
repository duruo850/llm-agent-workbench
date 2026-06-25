from __future__ import annotations

from decimal import Decimal

from server.model.base import ResponseBase


class CategorySummaryResponse(ResponseBase):
    """月度汇总中单个分类的统计。"""

    category: str
    total_amount: Decimal
    transaction_count: int
    budget_limit: Decimal | None = None
    over_budget: bool | None = None  # 无预算时为 None


class MonthlySummaryResponse(ResponseBase):
    """GET /summary/monthly 响应。"""

    month: str
    categories: list[CategorySummaryResponse]
    total_amount: Decimal
    total_count: int
