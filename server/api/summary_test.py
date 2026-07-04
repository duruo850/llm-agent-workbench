"""Summary API 集成测试 — GET /summary。"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

from utils.date_range import bounds_from_period

TEST_MONTH = "2025-06"


def test_summary_month(http_client: httpx.Client, transaction: dict[str, Any]) -> None:
    start, end = bounds_from_period("month", TEST_MONTH)
    response = http_client.get(
        "/summary",
        params={
            "period": "month",
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
    )
    response.raise_for_status()
    body = response.json()
    assert body["period"] == "month"
    assert body["total_count"] >= 1
    assert Decimal(str(body["total_amount"])) >= Decimal(str(transaction["amount"]))


def test_summary_day(http_client: httpx.Client, transaction: dict[str, Any]) -> None:
    day = transaction["transacted_at"][:10]
    start, end = bounds_from_period("day", day)
    response = http_client.get(
        "/summary",
        params={
            "period": "day",
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
    )
    response.raise_for_status()
    body = response.json()
    assert body["period"] == "day"
    assert body["total_count"] >= 1
    assert Decimal(str(body["total_amount"])) >= Decimal(str(transaction["amount"]))


def test_summary_end_before_start(http_client: httpx.Client) -> None:
    response = http_client.get(
        "/summary",
        params={
            "period": "day",
            "start": "2025-06-02T00:00:00",
            "end": "2025-06-01T23:59:59",
        },
    )
    assert response.status_code == 400
