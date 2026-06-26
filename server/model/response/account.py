from __future__ import annotations

from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel


class AccountCreateResponse(SQLModel):
    """POST /accounts 响应（不含 token，登录接口单独返回）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class AccountUpdateResponse(SQLModel):
    """PATCH /accounts/{id} 响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class AccountGetResponse(SQLModel):
    """GET /accounts/{id} 响应。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class AccountListResponse(SQLModel):
    """GET /accounts 列表项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class AccountLoginResponse(SQLModel):
    """POST /accounts/login 响应。"""

    model_config = ConfigDict(from_attributes=True)

    token: str
    account_id: int
    name: str
