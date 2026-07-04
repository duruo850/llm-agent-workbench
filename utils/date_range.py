"""日期区间工具。"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("Asia/Shanghai")

Period = Literal["hour", "day", "week", "month", "year"]


def month_range(month: str) -> tuple[datetime, datetime]:
    """将 ``YYYY-MM`` 解析为半开区间 ``[start, end)``，用于 ``transacted_at`` 过滤。"""
    start = datetime.strptime(f"{month}-01", "%Y-%m-%d")
    if start.month == 12:
        end = datetime(start.year + 1, 1, 1)
    else:
        end = datetime(start.year, start.month + 1, 1)
    return start, end


def day_range(date: str) -> tuple[datetime, datetime]:
    """将 ``YYYY-MM-DD`` 解析为半开区间 ``[start, end)``，用于 ``transacted_at`` 过滤。"""
    start = datetime.strptime(date, "%Y-%m-%d")
    return start, start + timedelta(days=1)


def parse_cst_datetime(s: str) -> datetime:
    """解析 ISO / ``YYYY-MM-DD`` / ``YYYY-MM-DD HH:MM:SS``，产出 naive CST datetime。"""
    text = s.strip()
    if "T" in text:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            dt = dt.astimezone(APP_TZ).replace(tzinfo=None)
        return dt.replace(microsecond=0)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).replace(microsecond=0)
        except ValueError:
            continue
    raise ValueError(f"无法解析日期时间: {s!r}")


def _end_of_month(year: int, month: int) -> datetime:
    if month == 12:
        return datetime(year, 12, 31, 23, 59, 59)
    next_month = datetime(year, month + 1, 1)
    last_day = next_month - timedelta(seconds=1)
    return last_day.replace(hour=23, minute=59, second=59, microsecond=0)


def bounds_from_period(period: Period, anchor: str) -> tuple[datetime, datetime]:
    """按 period 将锚点换算为闭区间 ``[start, end]``（naive CST）。"""
    if period == "hour":
        dt = parse_cst_datetime(anchor)
        start = dt.replace(minute=0, second=0, microsecond=0)
        end = start.replace(minute=59, second=59)
        return start, end

    if period == "day":
        if len(anchor.strip()) == 10 and anchor[4] == "-" and anchor[7] == "-":
            day = datetime.strptime(anchor.strip(), "%Y-%m-%d")
        else:
            day = parse_cst_datetime(anchor).replace(hour=0, minute=0, second=0, microsecond=0)
        start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        end = day.replace(hour=23, minute=59, second=59, microsecond=0)
        return start, end

    if period == "week":
        dt = parse_cst_datetime(anchor)
        monday = dt - timedelta(days=dt.weekday())
        start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        sunday = start + timedelta(days=6)
        end = sunday.replace(hour=23, minute=59, second=59, microsecond=0)
        return start, end

    if period == "month":
        text = anchor.strip()
        if len(text) == 7 and text[4] == "-":
            year, month = map(int, text.split("-"))
            start = datetime(year, month, 1)
        else:
            dt = parse_cst_datetime(anchor)
            start = datetime(dt.year, dt.month, 1)
        end = _end_of_month(start.year, start.month)
        return start, end

    if period == "year":
        text = anchor.strip()
        if len(text) == 4 and text.isdigit():
            year = int(text)
        else:
            year = parse_cst_datetime(anchor).year
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31, 23, 59, 59)
        return start, end

    raise ValueError(f"不支持的 period: {period!r}")
