"""Transaction HTTP API — 编排层，业务逻辑走 ``transaction_service``。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from server.service.account import get_current_account
from server.model.account import Account
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
    account: Account = Depends(get_current_account),
) -> TransactionCreateResponse:
    return await transaction_service.create_transaction(
        db, body, account_id=account.id
    )


@router.get("/{transaction_id}", response_model=TransactionGetResponse)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> TransactionGetResponse:
    row = await transaction_service.get_transaction(
        db, transaction_id, account_id=account.id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return row


@router.get("", response_model=list[TransactionListResponse])
async def list_transactions(
    query: Annotated[TransactionListQueryRequest, Depends()],
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> list[TransactionListResponse]:
    return await transaction_service.list_transactions(
        db, account_id=account.id, month=query.month
    )


@router.patch("/{transaction_id}", response_model=TransactionUpdateResponse)
async def update_transaction(
    transaction_id: int,
    body: TransactionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> TransactionUpdateResponse:
    row = await transaction_service.update_transaction(
        db, transaction_id, body, account_id=account.id
    )
    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return row


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> None:
    deleted = await transaction_service.delete_transaction(
        db, transaction_id, account_id=account.id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found")
