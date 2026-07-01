"""Account 业务服务 — 增删改查 + 登录 / 鉴权。"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from server.model.account import Account
from server.model.request.account import AccountCreateRequest, AccountUpdateRequest
from server.model.response.account import (
    AccountCreateResponse,
    AccountGetResponse,
    AccountListResponse,
    AccountUpdateResponse,
)
from storage.postgres.service.base import PaginatedList
from storage.postgres.service.enter import account_crud
from utils.bearer_token import parse_bearer_token


class AccountService:
    async def create_account(
        self,
        db: AsyncSession,
        body: AccountCreateRequest,
        *,
        token: str | None = None,
    ) -> AccountCreateResponse:
        payload = Account(name=body.name, token=token or str(uuid.uuid4()))
        created = await account_crud.create(
            db,
            object=payload,
            schema_to_select=AccountCreateResponse,
            return_as_model=True,
        )
        if created is None:
            raise RuntimeError("create account returned None")
        return created

    async def get_account(
        self, db: AsyncSession, account_id: int
    ) -> AccountGetResponse | None:
        return await account_crud.get(
            db,
            id=account_id,
            schema_to_select=AccountGetResponse,
            return_as_model=True,
            one_or_none=True,
        )

    async def list_accounts(
        self,
        db: AsyncSession,
        *,
        offset: int = 0,
        limit: int | None = 100,
    ) -> PaginatedList[AccountListResponse]:
        result = await account_crud.get_multi(
            db,
            offset=offset,
            limit=limit,
            schema_to_select=AccountListResponse,
            return_as_model=True,
        )
        return PaginatedList(data=result["data"], total_count=result["total_count"])

    async def update_account(
        self,
        db: AsyncSession,
        account_id: int,
        body: AccountUpdateRequest,
    ) -> AccountUpdateResponse | None:
        return await account_crud.update(
            db,
            object=body,
            id=account_id,
            schema_to_select=AccountUpdateResponse,
            return_as_model=True,
            one_or_none=True,
        )

    async def delete_account(self, db: AsyncSession, account_id: int) -> bool:
        existing = await account_crud.get(db, id=account_id)
        if existing is None:
            return False
        await account_crud.delete(db, id=account_id)
        return True

    async def get_account_model(
        self, db: AsyncSession, account_id: int
    ) -> Account | None:
        return await account_crud.get(
            db,
            id=account_id,
            schema_to_select=Account,
            return_as_model=True,
            one_or_none=True,
        )

    async def get_by_name(self, db: AsyncSession, name: str) -> Account | None:
        return await account_crud.get(
            db,
            name=name.strip(),
            schema_to_select=Account,
            return_as_model=True,
            one_or_none=True,
        )

    async def get_by_token(self, db: AsyncSession, token: str) -> Account | None:
        return await account_crud.get(
            db,
            token=token,
            schema_to_select=Account,
            return_as_model=True,
            one_or_none=True,
        )

    async def login_or_register(self, db: AsyncSession, name: str) -> Account:
        """按 name 查账号；存在则刷新 token，不存在则创建。"""
        stripped = name.strip()
        new_token = str(uuid.uuid4())
        account = await self.get_by_name(db, stripped)
        if account is None:
            created = await self.create_account(
                db, AccountCreateRequest(name=stripped), token=new_token
            )
            loaded = await self.get_account_model(db, created.id)
            if loaded is None:
                raise RuntimeError("create account not found after insert")
            return loaded
        await account_crud.update(db, object={"token": new_token}, id=account.id)
        refreshed = await self.get_account_model(db, account.id)
        if refreshed is None:
            raise RuntimeError("account not found after token refresh")
        return refreshed

    async def get_current_account(
        self, db: AsyncSession, authorization: str | None
    ) -> Account:
        """解析 Authorization Bearer 并返回当前账号；格式或 token 非法时抛 ValueError。"""
        token = parse_bearer_token(authorization)
        account = await self.get_by_token(db, token)
        if account is None:
            raise ValueError("invalid token")
        return account


account_service = AccountService()


async def get_current_account(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
) -> Account:
    """FastAPI 依赖 — 解析 Bearer 并返回当前账号。"""
    try:
        return await account_service.get_current_account(db, authorization)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
