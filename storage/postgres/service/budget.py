"""Budget 业务服务 — 增删改查（按 account 隔离）。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from server.model.budget import Budget
from storage.postgres.service.enter import budget_crud, category_crud
from server.model.request import BudgetCreateRequest, BudgetUpdateRequest
from server.model.response import (
    BudgetCreateResponse,
    BudgetGetResponse,
    BudgetListResponse,
    BudgetUpdateResponse,
)
from storage.postgres.service.base import PaginatedList


class BudgetService:
    async def create_budget(
        self,
        db: AsyncSession,
        body: BudgetCreateRequest,
        *,
        account_id: int,
    ) -> BudgetCreateResponse | None:
        category = await category_crud.get(
            db, id=body.category_id, account_id=account_id, one_or_none=True
        )
        if category is None:
            return None
        payload = Budget(**body.model_dump(), account_id=account_id)
        created = await budget_crud.create(
            db,
            object=payload,
            schema_to_select=BudgetCreateResponse,
            return_as_model=True,
        )
        if created is None:
            raise RuntimeError("create budget returned None")
        return created

    async def get_budget(
        self, db: AsyncSession, budget_id: int, *, account_id: int
    ) -> BudgetGetResponse | None:
        return await budget_crud.get(
            db,
            id=budget_id,
            account_id=account_id,
            schema_to_select=BudgetGetResponse,
            return_as_model=True,
            one_or_none=True,
        )

    async def list_budgets(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        offset: int = 0,
        limit: int | None = 100,
    ) -> PaginatedList[BudgetListResponse]:
        result = await budget_crud.get_multi(
            db,
            account_id=account_id,
            offset=offset,
            limit=limit,
            schema_to_select=BudgetListResponse,
            return_as_model=True,
        )
        return PaginatedList(data=result["data"], total_count=result["total_count"])

    async def update_budget(
        self,
        db: AsyncSession,
        budget_id: int,
        body: BudgetUpdateRequest,
        *,
        account_id: int,
    ) -> BudgetUpdateResponse | None:
        return await budget_crud.update(
            db,
            object=body,
            id=budget_id,
            account_id=account_id,
            schema_to_select=BudgetUpdateResponse,
            return_as_model=True,
            one_or_none=True,
        )

    async def delete_budget(
        self, db: AsyncSession, budget_id: int, *, account_id: int
    ) -> bool:
        existing = await budget_crud.get(db, id=budget_id, account_id=account_id)
        if existing is None:
            return False
        await budget_crud.delete(db, id=budget_id, account_id=account_id)
        return True


budget_service = BudgetService()
