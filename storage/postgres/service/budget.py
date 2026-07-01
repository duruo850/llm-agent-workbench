"""Budget 业务服务 - 薄 CRUD, 入参/出参均为 ``Budget`` 模型."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from server.model.budget import Budget
from server.model.request.budget import BudgetListQueryRequest
from storage.postgres.service.enter import budget_crud


@dataclass
class BudgetList:
    data: list[Budget]
    total_count: int


class BudgetService:
    async def create(self, db: AsyncSession, budget: Budget) -> Budget:
        created = await budget_crud.create(
            db,
            object=budget,
            schema_to_select=Budget,
            return_as_model=True,
        )
        if created is None:
            raise RuntimeError("create budget returned None")
        return created

    async def get_list(
        self,
        db: AsyncSession,
        req: BudgetListQueryRequest,
    ) -> BudgetList:
        filters: dict[str, object] = {}
        if req.Id is not None:
            filters["id"] = req.Id
        if req.AccountId is not None:
            filters["account_id"] = req.AccountId
        if req.CategoryId is not None:
            filters["category_id"] = req.CategoryId
        if req.Month:
            filters["month"] = req.Month
        result = await budget_crud.get_multi(
            db,
            **filters,
            offset=req.Page * req.PageSize,
            limit=req.PageSize,
            schema_to_select=Budget,
            return_as_model=True,
        )
        return BudgetList(data=result["data"], total_count=result["total_count"])

    async def update(self, db: AsyncSession, budget: Budget) -> Budget | None:
        return await budget_crud.update(
            db,
            object={
                "category_id": budget.category_id,
                "month": budget.month,
                "limit_amount": budget.limit_amount,
            },
            id=budget.id,
            account_id=budget.account_id,
            schema_to_select=Budget,
            return_as_model=True,
            one_or_none=True,
        )

    async def delete(self, db: AsyncSession, budget: Budget) -> None:
        await budget_crud.delete(db, id=budget.id, account_id=budget.account_id)


budget_service = BudgetService()
