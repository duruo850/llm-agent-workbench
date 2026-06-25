"""Transaction CRUD — POST/GET/PATCH/DELETE /transactions，及按月列表。"""

from __future__ import annotations

from typing import Any

import httpx

TEST_MONTH = "2025-06"


def test_create_transaction(http_client: httpx.Client, category: dict[str, Any]) -> None:
    response = http_client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": category["name"],
            "merchant": "便利店",
            "note": "创建测试",
            "transacted_at": f"{TEST_MONTH}-10T09:00:00",
        },
    )
    response.raise_for_status()
    body = response.json()
    assert body["category"] == category["name"]
    http_client.delete(f"/transactions/{body['id']}")


def test_get_transaction(http_client: httpx.Client, transaction: dict[str, Any]) -> None:
    response = http_client.get(f"/transactions/{transaction['id']}")
    response.raise_for_status()
    body = response.json()
    assert body["id"] == transaction["id"]
    assert body["merchant"] == transaction["merchant"]


def test_list_transactions_by_month(
    http_client: httpx.Client,
    transaction: dict[str, Any],
) -> None:
    response = http_client.get("/transactions", params={"month": TEST_MONTH})
    response.raise_for_status()
    body = response.json()
    assert isinstance(body, list)
    assert any(item["id"] == transaction["id"] for item in body)


def test_update_transaction(http_client: httpx.Client, transaction: dict[str, Any]) -> None:
    response = http_client.patch(f"/transactions/{transaction['id']}", json={"note": "午餐"})
    response.raise_for_status()
    response = http_client.get(f"/transactions/{transaction['id']}")
    response.raise_for_status()
    assert response.json()["note"] == "午餐"


def test_delete_transaction(http_client: httpx.Client, category: dict[str, Any]) -> None:
    response = http_client.post(
        "/transactions",
        json={
            "amount": 1,
            "category": category["name"],
            "merchant": "待删",
            "note": "",
            "transacted_at": f"{TEST_MONTH}-11T10:00:00",
        },
    )
    response.raise_for_status()
    txn_id = response.json()["id"]
    response = http_client.delete(f"/transactions/{txn_id}")
    response.raise_for_status()
    assert http_client.get(f"/transactions/{txn_id}").status_code == 404
