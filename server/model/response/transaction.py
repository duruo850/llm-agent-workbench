from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import ConfigDict
from sqlmodel import SQLModel


class TransactionCreateResponse(SQLModel):
    """POST /transactions 响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    amount: Decimal
    category: str
    merchant: str
    note: str
    transacted_at: datetime
    created_at: datetime | None


class TransactionUpdateResponse(SQLModel):
    """PATCH /transactions/{id} 响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    category: str
    merchant: str
    note: str
    transacted_at: datetime
    created_at: datetime | None


class TransactionGetResponse(SQLModel):
    """GET /transactions/{id} 响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    category: str
    merchant: str
    note: str
    transacted_at: datetime
    created_at: datetime | None


class TransactionListResponse(SQLModel):
    """GET /transactions 列表项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    category: str
    merchant: str
    note: str
    transacted_at: datetime
    created_at: datetime | None


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
