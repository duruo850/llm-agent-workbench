from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from server.model.base import RequestBase


class BudgetCreateRequest(RequestBase):
    """POST /budgets — 创建预算。"""

    category_id: int
    month: str = Field(pattern=r"^\d{4}-\d{2}$")
    limit_amount: Decimal = Field(ge=0)


class BudgetUpdateRequest(RequestBase):
    """PATCH /budgets/{id} — 部分更新。"""

    category_id: int | None = None
    month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
    limit_amount: Decimal | None = Field(default=None, ge=0)


class BudgetListQueryRequest(RequestBase):
    """GET /budgets — 列表查询参数（分页由 FastCRUD 提供 offset/limit/sort）。"""

    pass
