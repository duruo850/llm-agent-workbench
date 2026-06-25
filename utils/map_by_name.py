"""按 name 属性建立索引的通用工具。"""

from __future__ import annotations

from typing import Iterable, Protocol, TypeVar


class _Named(Protocol):
    name: str


T = TypeVar("T", bound=_Named)


def map_by_name(items: Iterable[T]) -> dict[str, T]:
    """将带 ``name`` 属性的对象列表转为 ``name → 对象`` 字典。

    典型用途：LangChain ``BaseTool`` 列表按名称查找，供 tool_calls 分发。
    """
    return {item.name: item for item in items}
