"""Account HTTP API — POST /accounts/login（无需 Bearer）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from server.model.request.account import AccountLoginRequest
from server.model.response.account import AccountLoginResponse
from storage.postgres.service.account import account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/login", response_model=AccountLoginResponse)
async def login(
    body: AccountLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AccountLoginResponse:
    account = await account_service.login_or_register(db, body.name)
    return AccountLoginResponse(
        token=account.token, account_id=account.id, name=account.name
    )
