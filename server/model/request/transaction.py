from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Self

from pydantic import Field, model_validator

from server.model.base import RequestBase
from server.model.request.parsed import ParsedTransaction


class TransactionCreateRequest(RequestBase):
    """POST /transactions — 记一笔。"""

    amount: Decimal = Field(gt=0)
    category: str = Field(min_length=1, max_length=100)
    merchant: str = Field(default="", max_length=200)
    note: str = Field(default="", max_length=500)
    transacted_at: datetime | None = None

    @model_validator(mode="after")
    def default_transacted_at(self) -> Self:
        if self.transacted_at is None:
            self.transacted_at = datetime.now().replace(microsecond=0)
        return self

    @classmethod
    def from_parsed(
        cls,
        txn: ParsedTransaction,
        *,
        transacted_at: datetime | None = None,
    ) -> TransactionCreateRequest:
        """从 M0 LLM 解析结果构建 POST 请求体。"""
        return cls(
            amount=Decimal(str(txn.amount)),
            category=txn.category,
            merchant=txn.merchant,
            note=txn.note,
            transacted_at=transacted_at,
        )


class TransactionUpdateRequest(RequestBase):
    """PATCH /transactions/{id} — 部分更新。"""

    amount: Decimal | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    merchant: str | None = Field(default=None, max_length=200)
    note: str | None = Field(default=None, max_length=500)
    transacted_at: datetime | None = None


class TransactionListQueryRequest(RequestBase):
    """GET /transactions — 列表查询参数。"""

    month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$")
