"""汇总 API — 编排层,Response 在 API 组装。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from storage.postgres.service.account import get_current_account
from server.model.account import Account
from server.model.request import SummaryQueryRequest
from server.model.response import SummaryResponse
from storage.postgres.service.transaction import transaction_service
from utils.date_range import parse_cst_datetime

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("", response_model=SummaryResponse)
async def summary(
    query: Annotated[SummaryQueryRequest, Depends()],
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> SummaryResponse:
    start_dt = parse_cst_datetime(query.start)
    end_dt = parse_cst_datetime(query.end)
    if end_dt < start_dt:
        raise HTTPException(status_code=400, detail="end 必须 >= start")

    result = await transaction_service.get_summary(
        db,
        account_id=account.id,
        start=start_dt,
        end=end_dt,
    )
    return SummaryResponse(
        period=query.period,
        start=result.start,
        end=result.end,
        total_amount=result.total_amount,
        total_count=result.total_count,
    )
