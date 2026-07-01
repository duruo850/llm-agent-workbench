from __future__ import annotations

from decimal import Decimal

from pydantic import ConfigDict
from sqlmodel import SQLModel

from server.model.transaction import Transaction


class TransactionGetListResponse(SQLModel):
    """GET /transactions 响应（按月/按日列表）。"""

    model_config = ConfigDict(from_attributes=True)

    List: list[Transaction]


class TransactionImportCategorySummary(SQLModel):
    """CSV 导入按分类汇总。"""

    category: str
    count: int
    total_amount: Decimal


class TransactionImportResponse(SQLModel):
    """POST /transactions/import 响应。"""

    imported_count: int
    skipped_count: int
    errors: list[str]
    categories: list[TransactionImportCategorySummary]
