"""Budget API 集成测试 — POST/GET/PATCH/DELETE /budgets。"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import httpx

TEST_MONTH = "2025-06"


def test_create_budget(http_client: httpx.Client, category: dict[str, Any]) -> None:
    response = http_client.post(
        "/budgets",
        json={"category_id": category["id"], "month": TEST_MONTH, "limit_amount": 2000},
    )
    response.raise_for_status()
    body = response.json()
    assert body["category_id"] == category["id"]
    assert body["month"] == TEST_MONTH
    http_client.delete(f"/budgets/{body['id']}")


def test_get_budget(http_client: httpx.Client, budget: dict[str, Any]) -> None:
    response = http_client.get(f"/budgets/{budget['id']}")
    response.raise_for_status()
    body = response.json()
    assert body["id"] == budget["id"]
    assert body["category_id"] == budget["category_id"]


def test_list_budgets(http_client: httpx.Client, budget: dict[str, Any]) -> None:
    response = http_client.get("/budgets")
    response.raise_for_status()
    body = response.json()
    assert "data" in body
    assert any(item["id"] == budget["id"] for item in body["data"])


def test_update_budget(http_client: httpx.Client, budget: dict[str, Any]) -> None:
    response = http_client.patch(f"/budgets/{budget['id']}", json={"limit_amount": 3000})
    response.raise_for_status()
    response = http_client.get(f"/budgets/{budget['id']}")
    response.raise_for_status()
    assert Decimal(str(response.json()["limit_amount"])) == Decimal("3000")


def test_delete_budget(http_client: httpx.Client, category: dict[str, Any]) -> None:
    response = http_client.post(
        "/budgets",
        json={"category_id": category["id"], "month": "2099-01", "limit_amount": 500},
    )
    response.raise_for_status()
    budget_id = response.json()["id"]
    response = http_client.delete(f"/budgets/{budget_id}")
    response.raise_for_status()
    assert http_client.get(f"/budgets/{budget_id}").status_code == 404
