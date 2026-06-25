from __future__ import annotations

from decimal import Decimal

from pydantic import ConfigDict
from sqlmodel import SQLModel


class BudgetCreateResponse(SQLModel):
    """POST /budgets 响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    month: str
    limit_amount: Decimal


class BudgetUpdateResponse(SQLModel):
    """PATCH /budgets/{id} 响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    month: str
    limit_amount: Decimal


class BudgetGetResponse(SQLModel):
    """GET /budgets/{id} 响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    month: str
    limit_amount: Decimal


class BudgetListResponse(SQLModel):
    """GET /budgets 列表项（FastCRUD 分页 data 元素）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    month: str
    limit_amount: Decimal
