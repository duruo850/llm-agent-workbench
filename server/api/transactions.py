"""Transaction HTTP API — 编排层，业务逻辑走 ``transaction_service``。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from server.model.request import TransactionCreateRequest, TransactionListQueryRequest, TransactionUpdateRequest
from server.model.response import (
    TransactionCreateResponse,
    TransactionGetResponse,
    TransactionListResponse,
    TransactionUpdateResponse,
)
from server.service import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionCreateResponse)
async def create_transaction(
    body: TransactionCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> TransactionCreateResponse:
    return await transaction_service.create_transaction(db, body)


@router.get("/{transaction_id}", response_model=TransactionGetResponse)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
) -> TransactionGetResponse:
    row = await transaction_service.get_transaction(db, transaction_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return row


@router.get("", response_model=list[TransactionListResponse])
async def list_transactions(
    query: Annotated[TransactionListQueryRequest, Depends()],
    db: AsyncSession = Depends(get_db),
) -> list[TransactionListResponse]:
    return await transaction_service.list_transactions(db, month=query.month)


@router.patch("/{transaction_id}", response_model=TransactionUpdateResponse)
async def update_transaction(
    transaction_id: int,
    body: TransactionUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> TransactionUpdateResponse:
    row = await transaction_service.update_transaction(db, transaction_id, body)
    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return row


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    deleted = await transaction_service.delete_transaction(db, transaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
