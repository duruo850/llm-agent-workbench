from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from server.model.account import Account
from server.model.base import RequestBase


class AccountCreateRequest(RequestBase):
    """POST /accounts — 创建账号（token 由 service 生成）."""

    Data: Account


class AccountUpdateRequest(RequestBase):
    """PATCH /accounts/{id} — 部分更新."""

    Data: Account


class AccountListQueryRequest(RequestBase):
    """GET /accounts — 列表查询参数."""

    Page: int = 0
    PageSize: int = 100
    Keyword: str | None = None
    Id: int | None = None
    Name: str = ""


class AccountRegisterRequest(RequestBase):
    """POST /accounts/register — 账号密码注册."""

    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("name", "password")
    @classmethod
    def strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("cannot be empty")
        return stripped


class AccountLoginRequest(RequestBase):
    """POST /accounts/login — 游客登录，或账号密码登录."""

    name: str | None = Field(default=None, max_length=100)
    password: str | None = Field(default=None, max_length=128)
    guest: bool = False

    @field_validator("name", "password")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def require_credentials_unless_guest(self) -> AccountLoginRequest:
        if self.guest:
            return self
        if not self.name or not self.password:
            raise ValueError("name and password are required unless guest=true")
        return self
