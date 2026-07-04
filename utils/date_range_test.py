"""date_range 单元测试 — CST 解析与 bounds_from_period。"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import pytest

from utils.date_range import bounds_from_period, parse_cst_datetime


def test_parse_cst_datetime_iso_date() -> None:
    assert parse_cst_datetime("2026-07-04") == datetime(2026, 7, 4)


def test_parse_cst_datetime_iso_with_time() -> None:
    assert parse_cst_datetime("2026-07-04T14:30:00") == datetime(2026, 7, 4, 14, 30)


def test_parse_cst_datetime_space_format() -> None:
    assert parse_cst_datetime("2026-07-04 14:30:00") == datetime(2026, 7, 4, 14, 30)


def test_parse_cst_datetime_utc_converts_to_cst() -> None:
    # 2026-07-04T00:00:00Z = 2026-07-04 08:00 CST
    assert parse_cst_datetime("2026-07-04T00:00:00Z") == datetime(2026, 7, 4, 8, 0)


def test_bounds_from_period_hour() -> None:
    start, end = bounds_from_period("hour", "2026-07-04T14:30:00")
    assert start == datetime(2026, 7, 4, 14, 0, 0)
    assert end == datetime(2026, 7, 4, 14, 59, 59)


def test_bounds_from_period_day() -> None:
    start, end = bounds_from_period("day", "2026-07-04")
    assert start == datetime(2026, 7, 4, 0, 0, 0)
    assert end == datetime(2026, 7, 4, 23, 59, 59)


def test_bounds_from_period_week_iso_monday_sunday() -> None:
    # 2026-07-04 是周六；ISO 周从周一开始
    start, end = bounds_from_period("week", "2026-07-04")
    assert start == datetime(2026, 6, 29, 0, 0, 0)  # 周一
    assert end == datetime(2026, 7, 5, 23, 59, 59)  # 周日


def test_bounds_from_period_month() -> None:
    start, end = bounds_from_period("month", "2026-02")
    assert start == datetime(2026, 2, 1)
    assert end == datetime(2026, 2, 28, 23, 59, 59)


def test_bounds_from_period_month_leap_year() -> None:
    start, end = bounds_from_period("month", "2024-02")
    assert end == datetime(2024, 2, 29, 23, 59, 59)


def test_bounds_from_period_year() -> None:
    start, end = bounds_from_period("year", "2026")
    assert start == datetime(2026, 1, 1)
    assert end == datetime(2026, 12, 31, 23, 59, 59)


def test_parse_cst_datetime_invalid() -> None:
    with pytest.raises(ValueError, match="无法解析"):
        parse_cst_datetime("not-a-date")
