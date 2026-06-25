from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import ConfigDict
from sqlmodel import SQLModel


class TransactionCreateResponse(SQLModel):
    """POST /transactions 响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
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
