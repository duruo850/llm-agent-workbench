from __future__ import annotations

from server.model.base import RequestBase
from server.model.category import Category


class CategoryCreateRequest(RequestBase):
    """POST /categories — 创建分类."""

    Data: Category


class CategoryUpdateRequest(RequestBase):
    """PATCH /categories/{id} — 部分更新."""

    Data: Category


class CategoryListQueryRequest(RequestBase):
    """GET /categories — 列表查询参数."""

    Page: int = 0
    PageSize: int = 100
    Keyword: str | None = None
    Id: int | None = None
    AccountId: int | None = None
    Name: str = ""
