from __future__ import annotations

from decimal import Decimal

from pydantic import Field

from server.model.base import RequestBase


class CategoryCreateRequest(RequestBase):
    """POST /categories — 创建分类。"""

    name: str = Field(min_length=1, max_length=100)
    budget_monthly: Decimal | None = Field(default=None, ge=0)


class CategoryUpdateRequest(RequestBase):
    """PATCH /categories/{id} — 部分更新。"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    budget_monthly: Decimal | None = Field(default=None, ge=0)


class CategoryListQueryRequest(RequestBase):
    """GET /categories — 列表查询参数（分页由 FastCRUD 提供 offset/limit/sort）。"""

    pass
