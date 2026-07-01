"""Transaction HTTP API — 编排层，Request/Response 与 ``Transaction`` 模型转换。"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent.common.parse_sentence import parse_sentence
from common.csv_import import import_csv_transactions
from server.db.session import get_db
from storage.postgres.service.account import get_current_account
from server.model.account import Account
from server.model.request import TransactionCreateRequest, TransactionListQueryRequest, TransactionUpdateRequest
from server.model.transaction import Transaction
from server.model.response import (
    TransactionGetListResponse,
    TransactionImportCategorySummary,
    TransactionImportResponse,
)
from storage.postgres.service.transaction import transaction_service

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=Transaction)
async def create_transaction(
    body: TransactionCreateRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> Transaction:
    row = body.Data
    row.account_id = account.id
    if isinstance(row.transacted_at, str):
        row.transacted_at = datetime.fromisoformat(row.transacted_at)
    return await transaction_service.create(db, row)


@router.post("/import", response_model=TransactionImportResponse)
async def import_transactions_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> TransactionImportResponse:
    content = await file.read()
    if not content.strip():
        raise HTTPException(status_code=400, detail="empty file")

    result = await import_csv_transactions(
        db,
        account_id=account.id,
        content=content,
        parse_sentence=parse_sentence,
    )
    if result.imported_count == 0:
        raise HTTPException(
            status_code=400,
            detail={"errors": result.errors},
        )

    return TransactionImportResponse(
        imported_count=result.imported_count,
        skipped_count=result.skipped_count,
        errors=result.errors,
        categories=[
            TransactionImportCategorySummary(
                category=item.category,
                count=item.count,
                total_amount=item.total_amount,
            )
            for item in result.categories
        ],
    )


@router.get("/{transaction_id}", response_model=Transaction)
async def get_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> Transaction:
    result = await transaction_service.get_list(
        db,
        TransactionListQueryRequest(
            Id=transaction_id,
            AccountId=account.id,
            Page=0,
            PageSize=1,
        ),
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return result.data[0]


@router.get("", response_model=TransactionGetListResponse)
async def list_transactions(
    query: Annotated[TransactionListQueryRequest, Depends()],
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> TransactionGetListResponse:
    query.AccountId = account.id
    result = await transaction_service.get_list(db, query)
    return TransactionGetListResponse(List=result.data)


@router.patch("/{transaction_id}", response_model=Transaction)
async def update_transaction(
    body: TransactionUpdateRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> Transaction:
    row = body.Data
    row.account_id = account.id
    if isinstance(row.transacted_at, str):
        row.transacted_at = datetime.fromisoformat(row.transacted_at)
    updated = await transaction_service.update(db, row)
    if updated is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return updated


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> None:
    result = await transaction_service.get_list(
        db,
        TransactionListQueryRequest(
            Id=transaction_id,
            AccountId=account.id,
            Page=0,
            PageSize=1,
        ),
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Transaction not found")
    existing = result.data[0]
    await transaction_service.delete(db, existing)
