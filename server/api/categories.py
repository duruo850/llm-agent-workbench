"""Category HTTP API — 编排层，业务逻辑走 ``category_service``。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from server.model.account import Account
from server.service.account import get_current_account
from server.model.request import CategoryCreateRequest, CategoryUpdateRequest
from server.model.response import (
    CategoryCreateResponse,
    CategoryGetResponse,
    CategoryListResponse,
    CategoryUpdateResponse,
)
from server.service import category_service
from server.service.base import PaginatedList

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryCreateResponse)
async def create_category(
    body: CategoryCreateRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> CategoryCreateResponse:
    return await category_service.create_category(db, body, account_id=account.id)


@router.get("/{category_id}", response_model=CategoryGetResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> CategoryGetResponse:
    row = await category_service.get_category(db, category_id, account_id=account.id)
    if row is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return row


@router.get("", response_model=PaginatedList[CategoryListResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int | None, Query(ge=1, le=1000)] = 100,
) -> PaginatedList[CategoryListResponse]:
    return await category_service.list_categories(
        db, account_id=account.id, offset=offset, limit=limit
    )


@router.patch("/{category_id}", response_model=CategoryUpdateResponse)
async def update_category(
    category_id: int,
    body: CategoryUpdateRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> CategoryUpdateResponse:
    row = await category_service.update_category(
        db, category_id, body, account_id=account.id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return row


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> None:
    deleted = await category_service.delete_category(
        db, category_id, account_id=account.id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Category not found")
