"""Account 业务服务 - 薄 CRUD + 登录 / 鉴权, 入出均为 ``Account`` 模型."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from server.model.account import Account
from server.model.request.account import AccountListQueryRequest
from storage.postgres.service.enter import account_crud
from utils.bearer_token import parse_bearer_token


@dataclass
class AccountList:
    data: list[Account]
    total_count: int


class AccountService:
    async def create(
        self,
        db: AsyncSession,
        account: Account,
    ) -> Account:
        created = await account_crud.create(
            db,
            object=account,
            schema_to_select=Account,
            return_as_model=True,
        )
        if created is None:
            raise RuntimeError("create account returned None")
        return created

    async def get_list(
        self,
        db: AsyncSession,
        req: AccountListQueryRequest,
    ) -> AccountList:
        filters: dict[str, object] = {}
        if req.Id is not None:
            filters["id"] = req.Id
        if req.Name:
            filters["name"] = req.Name.strip()
        result = await account_crud.get_multi(
            db,
            **filters,
            offset=req.Page * req.PageSize,
            limit=req.PageSize,
            schema_to_select=Account,
            return_as_model=True,
        )
        return AccountList(data=result["data"], total_count=result["total_count"])

    async def update(self, db: AsyncSession, account: Account) -> Account | None:
        return await account_crud.update(
            db,
            object={"name": account.name, "token": account.token},
            id=account.id,
            schema_to_select=Account,
            return_as_model=True,
            one_or_none=True,
        )

    async def delete(self, db: AsyncSession, account: Account) -> None:
        await account_crud.delete(db, id=account.id)

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
            return await self.create(
                db,
                Account(name=stripped, token=new_token),
            )
        await account_crud.update(db, object={"token": new_token}, id=account.id)
        refreshed = await self.get_by_name(db, stripped)
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
