"""Budget HTTP API — 编排层，业务逻辑走 ``budget_service``。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from server.model.request import BudgetCreateRequest, BudgetUpdateRequest
from server.model.response import (
    BudgetCreateResponse,
    BudgetGetResponse,
    BudgetListResponse,
    BudgetUpdateResponse,
)
from server.service import budget_service
from server.service.base import PaginatedList

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetCreateResponse)
async def create_budget(
    body: BudgetCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> BudgetCreateResponse:
    return await budget_service.create_budget(db, body)


@router.get("/{budget_id}", response_model=BudgetGetResponse)
async def get_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
) -> BudgetGetResponse:
    row = await budget_service.get_budget(db, budget_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return row


@router.get("", response_model=PaginatedList[BudgetListResponse])
async def list_budgets(
    db: AsyncSession = Depends(get_db),
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(ge=1, le=1000)] = 100,
) -> PaginatedList[BudgetListResponse]:
    return await budget_service.list_budgets(db, offset=offset, limit=limit)


@router.patch("/{budget_id}", response_model=BudgetUpdateResponse)
async def update_budget(
    budget_id: int,
    body: BudgetUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> BudgetUpdateResponse:
    row = await budget_service.update_budget(db, budget_id, body)
    if row is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return row


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await budget_service.delete_budget(db, budget_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Budget not found")
