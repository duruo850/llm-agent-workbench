"""月度汇总 API — 编排层，业务逻辑在 ``transaction_service.get_monthly_summary``。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from storage.postgres.service.account import get_current_account
from server.model.account import Account
from server.model.request import MonthlySummaryQueryRequest
from server.model.response import MonthlySummaryResponse
from storage.postgres.service.transaction import transaction_service

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/monthly", response_model=MonthlySummaryResponse)
async def monthly_summary(
    query: Annotated[MonthlySummaryQueryRequest, Depends()],
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> MonthlySummaryResponse:
    return await transaction_service.get_monthly_summary(
        db, account_id=account.id, month=query.month
    )
