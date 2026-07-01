from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field

from server.model.base import RequestBase
from server.model.request.parsed import ParsedTransaction
from server.model.transaction import Transaction


class TransactionCreateRequest(RequestBase):
    """POST /transactions — 记一笔."""

    Data: Transaction

    @classmethod
    def from_parsed(
        cls,
        txn: ParsedTransaction,
        *,
        account_id: int,
        transacted_at: datetime | None = None,
    ) -> TransactionCreateRequest:
        """从 M0 LLM 解析结果构建 POST 请求体。"""
        when = transacted_at or datetime.now().replace(microsecond=0)
        return cls(
            Data=Transaction(
                account_id=account_id,
                amount=Decimal(str(txn.amount)),
                category=txn.category,
                merchant=txn.merchant,
                note=txn.note,
                transacted_at=when,
            )
        )


class TransactionUpdateRequest(RequestBase):
    """PATCH /transactions/{id} — 部分更新."""

    Data: Transaction


class TransactionListQueryRequest(RequestBase):
    """GET /transactions — 列表查询参数."""

    Page: int = 0
    PageSize: int = 100
    Keyword: str | None = None
    Id: int | None = None
    AccountId: int | None = None
    Month: str = Field(default="", alias="month")
    Date: str = Field(default="", alias="date")
    Category: str = Field(default="", alias="category")

    model_config = RequestBase.model_config | {"populate_by_name": True}
