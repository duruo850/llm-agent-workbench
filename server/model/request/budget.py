from __future__ import annotations

from server.model.base import RequestBase
from server.model.budget import Budget


class BudgetCreateRequest(RequestBase):
    """POST /budgets — 创建预算."""

    Data: Budget


class BudgetUpdateRequest(RequestBase):
    """PATCH /budgets/{id} — 部分更新."""

    Data: Budget


class BudgetListQueryRequest(RequestBase):
    """GET /budgets — 列表查询参数."""

    Page: int = 0
    PageSize: int = 100
    Keyword: str | None = None
    Id: int | None = None
    AccountId: int | None = None
    CategoryId: int | None = None
    Month: str = ""
