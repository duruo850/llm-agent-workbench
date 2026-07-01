from __future__ import annotations

from pydantic import ConfigDict
from sqlmodel import SQLModel

from server.model.account import Account


class AccountGetListResponse(SQLModel):
    """GET /accounts 响应."""

    model_config = ConfigDict(from_attributes=True)

    List: list[Account]
    TotalCount: int


class AccountLoginResponse(SQLModel):
    """POST /accounts/login 响应."""

    model_config = ConfigDict(from_attributes=True)

    token: str
    account_id: int
    name: str
