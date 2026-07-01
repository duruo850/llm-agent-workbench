from __future__ import annotations

from pydantic import ConfigDict
from sqlmodel import SQLModel

from server.model.category import Category


class CategoryGetListResponse(SQLModel):
    """GET /categories 响应."""

    model_config = ConfigDict(from_attributes=True)

    List: list[Category]
    TotalCount: int
