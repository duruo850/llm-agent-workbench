"""Category HTTP API — 编排层，Request/Response 与 ``Category`` 模型转换。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from server.model.account import Account
from server.model.category import Category
from storage.postgres.service.account import get_current_account
from server.model.request import CategoryCreateRequest, CategoryListQueryRequest, CategoryUpdateRequest
from server.model.response import CategoryGetListResponse
from storage.postgres.service import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=Category)
async def create_category(
    body: CategoryCreateRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> Category:
    if body.Data.account_id != account.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return await category_service.create(db, body.Data)


@router.get("/{category_id}", response_model=Category)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> Category:
    categoryRes = await category_service.get_list(
        db,
        CategoryListQueryRequest(Id=category_id, AccountId=account.id, Page=0, PageSize=1),
    )
    if not categoryRes.data:
        raise HTTPException(status_code=404, detail="Category not found")
    return categoryRes.data[0]


@router.get("", response_model=CategoryGetListResponse)
async def list_categories(
    query: Annotated[CategoryListQueryRequest, Depends()],
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> CategoryGetListResponse:
    query.AccountId = account.id
    result = await category_service.get_list(db, query)
    return CategoryGetListResponse(List=result.data, TotalCount=result.total_count)


@router.patch("/{category_id}", response_model=Category)
async def update_category(
    body: CategoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> Category:
    if body.Data.account_id != account.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    updated = await category_service.update(db, body.Data)
    if updated is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return updated


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> None:
    await category_service.delete(db, Category(id=category_id, account_id=account.id))
