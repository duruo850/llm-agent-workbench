"""Account 业务服务 - 薄 CRUD + 登录 / 鉴权, 入出均为 ``Account`` 模型."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from server.model.account import Account
from server.model.request.account import AccountListQueryRequest
from storage.postgres.service.enter import account_crud
from utils.bearer_token import parse_bearer_token
from utils.password import hash_password, verify_password

TOKEN_TTL = timedelta(minutes=10)


def _token_expiry(now: datetime | None = None) -> datetime:
    return (now or datetime.now()) + TOKEN_TTL


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
            object={
                "name": account.name,
                "token": account.token,
                "password_hash": account.password_hash,
                "token_expires_at": account.token_expires_at,
            },
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

    async def register(self, db: AsyncSession, name: str, password: str) -> Account:
        """账号密码注册；重名则 ValueError。密码仅存单向哈希。"""
        stripped = name.strip()
        if await self.get_by_name(db, stripped) is not None:
            raise ValueError("account already exists")
        return await self.create(
            db,
            Account(
                name=stripped,
                password_hash=hash_password(password),
                token=str(uuid.uuid4()),
                token_expires_at=_token_expiry(),
            ),
        )

    async def login_with_password(
        self, db: AsyncSession, name: str, password: str
    ) -> Account:
        """账号密码登录；失败抛 ValueError。"""
        account = await self.get_by_name(db, name.strip())
        if account is None or not account.password_hash:
            raise ValueError("invalid name or password")
        if not verify_password(password, account.password_hash):
            raise ValueError("invalid name or password")
        new_token = str(uuid.uuid4())
        await account_crud.update(
            db,
            object={"token": new_token, "token_expires_at": _token_expiry()},
            id=account.id,
        )
        refreshed = await self.get_by_name(db, name.strip())
        if refreshed is None:
            raise RuntimeError("account not found after token refresh")
        return refreshed

    async def login_or_register(
        self, db: AsyncSession, name: str, password: str = "dev"
    ) -> Account:
        """内部/CLI/测试：按 name 注册或密码登录（默认密码 ``dev``）。"""
        existing = await self.get_by_name(db, name.strip())
        if existing is None:
            return await self.register(db, name, password)
        return await self.login_with_password(db, name, password)

    async def login_as_guest(self, db: AsyncSession) -> Account:
        """游客登录：新建无密码 guest 账号并签发 token。"""
        guest_id = str(uuid.uuid4())
        return await self.create(
            db,
            Account(
                name=f"guest_{guest_id}",
                token=guest_id,
                password_hash=None,
                token_expires_at=_token_expiry(),
            ),
        )

    async def get_current_account(
        self, db: AsyncSession, authorization: str | None
    ) -> Account:
        """解析 Bearer；校验过期；未过期则滑动续期 10 分钟。"""
        token = parse_bearer_token(authorization)
        account = await self.get_by_token(db, token)
        if account is None:
            raise ValueError("invalid token")

        # 更新过期时间
        now = datetime.now()
        if account.token_expires_at is None or account.token_expires_at <= now:
            raise ValueError("token expired")
        new_expiry = _token_expiry(now)
        await account_crud.update(
            db,
            object={"token_expires_at": new_expiry},
            id=account.id,
        )
        account.token_expires_at = new_expiry
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
