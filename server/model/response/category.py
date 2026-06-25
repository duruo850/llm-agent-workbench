from __future__ import annotations

from decimal import Decimal

from pydantic import ConfigDict
from sqlmodel import SQLModel


class CategoryCreateResponse(SQLModel):
    """POST /categories 响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    budget_monthly: Decimal | None


class CategoryUpdateResponse(SQLModel):
    """PATCH /categories/{id} 响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    budget_monthly: Decimal | None


class CategoryGetResponse(SQLModel):
    """GET /categories/{id} 响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    budget_monthly: Decimal | None


class CategoryListResponse(SQLModel):
    """GET /categories 列表项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    budget_monthly: Decimal | None
