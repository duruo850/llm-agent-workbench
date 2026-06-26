from __future__ import annotations

from pydantic import Field, field_validator

from server.model.base import RequestBase


class AccountCreateRequest(RequestBase):
    """POST /accounts — 创建账号（token 由 service 生成）。"""

    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be empty")
        return stripped


class AccountUpdateRequest(RequestBase):
    """PATCH /accounts/{id} — 部分更新。"""

    name: str | None = Field(default=None, min_length=1, max_length=100)


class AccountListQueryRequest(RequestBase):
    """GET /accounts — 列表查询参数。"""

    pass


class AccountLoginRequest(RequestBase):
    """POST /accounts/login — 账号名登录（无密码）。"""

    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name cannot be empty")
        return stripped
