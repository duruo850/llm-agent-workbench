from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PageInfo(BaseModel):
    Page: int = 0
    PageSize: int = 100
    Keyword: str | None = None


class EntityBase(BaseModel):
    """领域实体基类（与 ORM 行可互转）。"""

    model_config = ConfigDict(from_attributes=True)


class RequestBase(PageInfo):
    """请求 schema 基类。"""

    model_config = ConfigDict(extra="forbid")


class ResponseBase(BaseModel):
    """响应 schema 基类。"""

    model_config = ConfigDict(from_attributes=True)
