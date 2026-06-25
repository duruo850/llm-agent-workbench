"""日期区间工具。"""

from __future__ import annotations

from datetime import datetime


def month_range(month: str) -> tuple[datetime, datetime]:
    """将 ``YYYY-MM`` 解析为半开区间 ``[start, end)``，用于 ``transacted_at`` 过滤。"""
    start = datetime.strptime(f"{month}-01", "%Y-%m-%d")
    if start.month == 12:
        end = datetime(start.year + 1, 1, 1)
    else:
        end = datetime(start.year, start.month + 1, 1)
    return start, end
