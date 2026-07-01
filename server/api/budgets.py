"""Budget HTTP API — 编排层，业务逻辑走 ``budget_service``。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from storage.postgres.service.account import get_current_account
from server.model.account import Account
from server.model.request import BudgetCreateRequest, BudgetUpdateRequest
from server.model.response import (
    BudgetCreateResponse,
    BudgetGetResponse,
    BudgetListResponse,
    BudgetUpdateResponse,
)
from storage.postgres.service.budget import budget_service
from storage.postgres.service.base import PaginatedList

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetCreateResponse)
async def create_budget(
    body: BudgetCreateRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> BudgetCreateResponse:
    return await budget_service.create_budget(db, body, account_id=account.id)


@router.get("/{budget_id}", response_model=BudgetGetResponse)
async def get_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> BudgetGetResponse:
    row = await budget_service.get_budget(db, budget_id, account_id=account.id)
    if row is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return row


@router.get("", response_model=PaginatedList[BudgetListResponse])
async def list_budgets(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(ge=1, le=1000)] = 100,
) -> PaginatedList[BudgetListResponse]:
    return await budget_service.list_budgets(
        db, account_id=account.id, offset=offset, limit=limit
    )


@router.patch("/{budget_id}", response_model=BudgetUpdateResponse)
async def update_budget(
    budget_id: int,
    body: BudgetUpdateRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> BudgetUpdateResponse:
    row = await budget_service.update_budget(
        db, budget_id, body, account_id=account.id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return row


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> None:
    deleted = await budget_service.delete_budget(db, budget_id, account_id=account.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Budget not found")
