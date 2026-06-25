"""按月查账等交易自定义查询。

``POST/PATCH/DELETE /transactions`` 由 FastCRUD 提供；
此处仅补充 ``GET /transactions?month=YYYY-MM``（半开区间过滤 ``transacted_at``）。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from utils.date_range import month_range
from server.crud.instances import transaction_crud
from server.model.transaction import Transaction
from server.db.session import get_db
from server.model.request import TransactionListQueryRequest
from server.model.response import TransactionListResponse

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionListResponse])
async def list_transactions(
    query: Annotated[TransactionListQueryRequest, Depends()],
    db: AsyncSession = Depends(get_db),
) -> list[TransactionListResponse]:
    stmt = await transaction_crud.select(
        schema_to_select=TransactionListResponse,
        sort_columns="transacted_at",
        sort_orders="desc",
    )
    if query.month:
        start, end = month_range(query.month)
        stmt = stmt.where(
            Transaction.transacted_at >= start,
            Transaction.transacted_at < end,
        )
    result = await db.execute(stmt)
    return [TransactionListResponse.model_validate(row) for row in result.mappings().all()]
