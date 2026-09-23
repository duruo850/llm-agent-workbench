"""Account HTTP API — register / login（游客或账号密码，无需 Bearer）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from server.model.request.account import AccountLoginRequest, AccountRegisterRequest
from server.model.response.account import AccountLoginResponse
from storage.postgres.service.account import account_service

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post("/register", response_model=AccountLoginResponse)
async def register(
    body: AccountRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AccountLoginResponse:
    try:
        account = await account_service.register(db, body.name, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return AccountLoginResponse(
        token=account.token, account_id=account.id, name=account.name
    )


@router.post("/login", response_model=AccountLoginResponse)
async def login(
    body: AccountLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AccountLoginResponse:
    if body.guest:
        account = await account_service.login_as_guest(db)
    else:
        if not body.name or not body.password:
            raise HTTPException(status_code=400, detail="name and password are required")
        try:
            account = await account_service.login_with_password(
                db, body.name, body.password
            )
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
    return AccountLoginResponse(
        token=account.token, account_id=account.id, name=account.name
    )
