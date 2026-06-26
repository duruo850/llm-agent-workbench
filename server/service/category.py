"""Category 业务服务 — 增删改查（按 account 隔离）。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from server.model.category import Category
from server.service.enter import category_crud
from server.model.request import CategoryCreateRequest, CategoryUpdateRequest
from server.model.response import (
    CategoryCreateResponse,
    CategoryGetResponse,
    CategoryListResponse,
    CategoryUpdateResponse,
)
from server.service.base import PaginatedList


class CategoryService:
    async def create_category(
        self,
        db: AsyncSession,
        body: CategoryCreateRequest,
        *,
        account_id: int,
    ) -> CategoryCreateResponse:
        payload = Category(**body.model_dump(), account_id=account_id)
        created = await category_crud.create(
            db,
            object=payload,
            schema_to_select=CategoryCreateResponse,
            return_as_model=True,
        )
        if created is None:
            raise RuntimeError("create category returned None")
        return created

    async def get_category(
        self, db: AsyncSession, category_id: int, *, account_id: int
    ) -> CategoryGetResponse | None:
        return await category_crud.get(
            db,
            id=category_id,
            account_id=account_id,
            schema_to_select=CategoryGetResponse,
            return_as_model=True,
            one_or_none=True,
        )

    async def list_categories(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        offset: int = 0,
        limit: int | None = 100,
    ) -> PaginatedList[CategoryListResponse]:
        result = await category_crud.get_multi(
            db,
            account_id=account_id,
            offset=offset,
            limit=limit,
            schema_to_select=CategoryListResponse,
            return_as_model=True,
        )
        return PaginatedList(data=result["data"], total_count=result["total_count"])

    async def update_category(
        self,
        db: AsyncSession,
        category_id: int,
        body: CategoryUpdateRequest,
        *,
        account_id: int,
    ) -> CategoryUpdateResponse | None:
        return await category_crud.update(
            db,
            object=body,
            id=category_id,
            account_id=account_id,
            schema_to_select=CategoryUpdateResponse,
            return_as_model=True,
            one_or_none=True,
        )

    async def delete_category(
        self, db: AsyncSession, category_id: int, *, account_id: int
    ) -> bool:
        existing = await category_crud.get(db, id=category_id, account_id=account_id)
        if existing is None:
            return False
        await category_crud.delete(db, id=category_id, account_id=account_id)
        return True


category_service = CategoryService()
