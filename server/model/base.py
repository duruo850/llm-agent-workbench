from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class EntityBase(BaseModel):
    """领域实体基类（与 ORM 行可互转）。"""

    model_config = ConfigDict(from_attributes=True)


class RequestBase(BaseModel):
    """请求 schema 基类。"""

    model_config = ConfigDict(extra="forbid")


class ResponseBase(BaseModel):
    """响应 schema 基类。"""

    model_config = ConfigDict(from_attributes=True)
