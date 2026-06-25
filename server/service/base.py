"""Service 层通用类型。"""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedList(BaseModel, Generic[T]):
    """分页列表，与 FastCRUD ``get_multi`` 响应结构一致。"""

    data: list[T]
    total_count: int
