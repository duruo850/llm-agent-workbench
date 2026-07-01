"""Category API 集成测试 — POST/GET/PATCH/DELETE /categories。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

from typing import Any

import httpx


def test_create_category(
    http_client: httpx.Client,
    account: dict[str, Any],
    unique_suffix: str,
) -> None:
    name = f"新建分类-{unique_suffix}"
    response = http_client.post(
        "/categories",
        json={
            "Data": {
                "name": name,
                "budget_monthly": 2000,
                "account_id": account["account_id"],
            }
        },
    )
    response.raise_for_status()
    body = response.json()
    assert body["name"] == name
    assert body["budget_monthly"] in ("2000.00", 2000, "2000")
    http_client.delete(f"/categories/{body['id']}")


def test_get_category(http_client: httpx.Client, category: dict[str, Any]) -> None:
    response = http_client.get(f"/categories/{category['id']}")
    response.raise_for_status()
    body = response.json()
    assert body["id"] == category["id"]
    assert body["name"] == category["name"]


def test_list_categories(http_client: httpx.Client, category: dict[str, Any]) -> None:
    response = http_client.get("/categories")
    response.raise_for_status()
    body = response.json()
    assert "List" in body
    assert any(item["id"] == category["id"] for item in body["List"])


def test_update_category(http_client: httpx.Client, category: dict[str, Any]) -> None:
    new_name = f"{category['name']}-更新"
    response = http_client.patch(
        f"/categories/{category['id']}",
        json={"Data": {**category, "name": new_name}},
    )
    response.raise_for_status()
    response = http_client.get(f"/categories/{category['id']}")
    response.raise_for_status()
    assert response.json()["name"] == new_name


def test_delete_category(
    http_client: httpx.Client,
    account: dict[str, Any],
    unique_suffix: str,
) -> None:
    response = http_client.post(
        "/categories",
        json={
            "Data": {
                "name": f"待删-{unique_suffix}",
                "account_id": account["account_id"],
            }
        },
    )
    response.raise_for_status()
    category_id = response.json()["id"]
    response = http_client.delete(f"/categories/{category_id}")
    response.raise_for_status()
    assert http_client.get(f"/categories/{category_id}").status_code == 404
