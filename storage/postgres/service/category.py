"""Category 业务服务 - 薄 CRUD, 入参/出参均为 ``Category`` 模型."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from server.model.category import Category
from server.model.request.category import CategoryListQueryRequest
from storage.postgres.service.enter import category_crud


@dataclass
class CategoryList:
    data: list[Category]
    total_count: int


class CategoryService:
    async def create(self, db: AsyncSession, category: Category) -> Category:
        created = await category_crud.create(
            db,
            object=category,
            schema_to_select=Category,
            return_as_model=True,
        )
        if created is None:
            raise RuntimeError("create category returned None")
        return created

    async def get_list(
        self,
        db: AsyncSession,
        req: CategoryListQueryRequest,
    ) -> CategoryList:
        filters: dict[str, object] = {}
        if req.Id is not None:
            filters["id"] = req.Id
        if req.AccountId is not None:
            filters["account_id"] = req.AccountId
        result = await category_crud.get_multi(
            db,
            **filters,
            offset=req.Page * req.PageSize,
            limit=req.PageSize,
            schema_to_select=Category,
            return_as_model=True,
        )
        return CategoryList(data=result["data"], total_count=result["total_count"])

    async def update(self, db: AsyncSession, category: Category) -> Category | None:
        return await category_crud.update(
            db,
            object={"name": category.name, "budget_monthly": category.budget_monthly},
            id=category.id,
            account_id=category.account_id,
            schema_to_select=Category,
            return_as_model=True,
            one_or_none=True,
        )

    async def delete(self, db: AsyncSession, category: Category) -> None:
        await category_crud.delete(
            db, id=category.id, account_id=category.account_id
        )


category_service = CategoryService()
