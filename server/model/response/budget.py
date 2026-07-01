from __future__ import annotations

from pydantic import ConfigDict
from sqlmodel import SQLModel

from server.model.budget import Budget


class BudgetGetListResponse(SQLModel):
    """GET /budgets 响应."""

    model_config = ConfigDict(from_attributes=True)

    List: list[Budget]
    TotalCount: int
