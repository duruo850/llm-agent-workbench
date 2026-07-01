"""Budget HTTP API — 编排层，Request/Response 与 ``Budget`` 模型转换。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from storage.postgres.service.account import get_current_account
from server.model.account import Account
from server.model.budget import Budget
from server.model.request import BudgetCreateRequest, BudgetListQueryRequest, BudgetUpdateRequest
from server.model.request.category import CategoryListQueryRequest
from server.model.response import BudgetGetListResponse
from storage.postgres.service.budget import budget_service
from storage.postgres.service.category import category_service

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=Budget)
async def create_budget(
    body: BudgetCreateRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> Budget:
    return await budget_service.create(db, body.Data)


@router.get("/{budget_id}", response_model=Budget)
async def get_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> Budget:
    budgetRes = await budget_service.get_list(
        db,
        BudgetListQueryRequest(Id=budget_id, AccountId=account.id, Page=0, PageSize=1),
    )
    if not budgetRes.data:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budgetRes.data[0]


@router.get("", response_model=BudgetGetListResponse)
async def list_budgets(
    query: Annotated[BudgetListQueryRequest, Depends()],
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> BudgetGetListResponse:
    result = await budget_service.get_list(db, query)
    return BudgetGetListResponse(List=result.data, TotalCount=result.total_count)


@router.patch("/{budget_id}", response_model=Budget)
async def update_budget(
    body: BudgetUpdateRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> Budget:
    if body.Data.account_id != account.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = await budget_service.update(db, body.Data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Budget not found")
    return updated


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> None:
    await budget_service.delete(db, Budget(id=budget_id, account_id=account.id))
