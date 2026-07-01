"""Transaction API 集成测试 — CRUD、按月列表、CSV 逐句导入。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import httpx

from common.test.resource_paths import resource_path
from server.api.conftest import _txn_list_rows

TEST_MONTH = "2025-06"


def _delete_import_test_rows(http_client: httpx.Client, prefix: str) -> None:
    response = http_client.get("/transactions", params={"month": TEST_MONTH})
    response.raise_for_status()
    for item in _txn_list_rows(response):
        merchant = item.get("merchant") or ""
        note = item.get("note") or ""
        if prefix in merchant or prefix in note:
            http_client.delete(f"/transactions/{item['id']}").raise_for_status()


def _post_csv_import(
    client: httpx.Client,
    csv_text: str | bytes,
    *,
    filename: str = "stmt.csv",
) -> httpx.Response:
    content = csv_text if isinstance(csv_text, bytes) else csv_text.encode()
    return client.post(
        "/transactions/import",
        files={"file": (filename, content, "text/csv")},
    )


def _import_csv_body(
    client: httpx.Client,
    csv_text: str | bytes,
    *,
    filename: str = "stmt.csv",
) -> dict[str, Any]:
    response = _post_csv_import(client, csv_text, filename=filename)
    response.raise_for_status()
    return response.json()


@contextmanager
def _import_test_cleanup(http_client: httpx.Client, prefix: str) -> Iterator[None]:
    try:
        yield
    finally:
        _delete_import_test_rows(http_client, prefix)


def test_create_transaction(http_client: httpx.Client, category: dict[str, Any]) -> None:
    response = http_client.post(
        "/transactions",
        json={
            "Data": {
                "amount": 50,
                "category": category["name"],
                "merchant": "便利店",
                "note": "创建测试",
                "transacted_at": f"{TEST_MONTH}-10T09:00:00",
                "account_id": category["account_id"],
            }
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
    rows = _txn_list_rows(response)
    assert any(item["id"] == transaction["id"] for item in rows)


def test_update_transaction(http_client: httpx.Client, transaction: dict[str, Any]) -> None:
    response = http_client.patch(
        f"/transactions/{transaction['id']}",
        json={"Data": {**transaction, "note": "午餐"}},
    )
    response.raise_for_status()
    response = http_client.get(f"/transactions/{transaction['id']}")
    response.raise_for_status()
    assert response.json()["note"] == "午餐"


def test_delete_transaction(http_client: httpx.Client, category: dict[str, Any]) -> None:
    response = http_client.post(
        "/transactions",
        json={
            "Data": {
                "amount": 1,
                "category": category["name"],
                "merchant": "待删",
                "note": "",
                "transacted_at": f"{TEST_MONTH}-11T10:00:00",
                "account_id": category["account_id"],
            }
        },
    )
    response.raise_for_status()
    txn_id = response.json()["id"]
    response = http_client.delete(f"/transactions/{txn_id}")
    response.raise_for_status()
    assert http_client.get(f"/transactions/{txn_id}").status_code == 404


def test_import_csv_success(
    http_client: httpx.Client,
    unique_suffix: str,
    require_llm: None,
) -> None:
    prefix = f"import-{unique_suffix}"
    csv_text = (
        f"在 {prefix}Starbucks 买咖啡花了 12.5 元，餐饮\n"
        f"坐 {prefix}地铁 花了 15 块，交通\n"
    )
    with _import_test_cleanup(http_client, prefix):
        body = _import_csv_body(http_client, csv_text)
        assert body["imported_count"] == 2
        assert body["skipped_count"] == 0
        assert body["errors"] == []
        assert len(body["categories"]) >= 1


def test_import_csv_partial_skips_non_bill(
    http_client: httpx.Client,
    unique_suffix: str,
    require_llm: None,
) -> None:
    prefix = f"partial-{unique_suffix}"
    csv_text = (
        f"在 {prefix}便利店 买水花了 10 元，餐饮\n"
        "今天天气不错\n"
    )
    with _import_test_cleanup(http_client, prefix):
        body = _import_csv_body(http_client, csv_text)
        assert body["imported_count"] == 1
        assert body["skipped_count"] == 1


def test_import_csv_from_sample_resource(
    http_client: httpx.Client,
    unique_suffix: str,
    require_llm: None,
) -> None:
    prefix = f"sample-{unique_suffix}"
    sample_lines = resource_path("sample_transactions.csv").read_text(encoding="utf-8").strip().splitlines()
    csv_text = f"在 {prefix}Starbucks 买咖啡花了 12.5 元，餐饮\n" + "\n".join(sample_lines[1:])
    with _import_test_cleanup(http_client, prefix):
        body = _import_csv_body(http_client, csv_text)
        assert body["imported_count"] >= 2
        assert body["skipped_count"] >= 1


def test_import_csv_unauthorized(http_client_no_auth: httpx.Client) -> None:
    response = _post_csv_import(http_client_no_auth, "地铁 6 块，交通\n")
    assert response.status_code == 401


def test_import_csv_empty_file(http_client: httpx.Client) -> None:
    response = _post_csv_import(http_client, b"", filename="empty.csv")
    assert response.status_code == 400
