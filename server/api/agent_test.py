"""Agent API HTTP 集成测试（真实 LLM，无 mock）。"""

from __future__ import annotations

import base64
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import pytest

TEST_MONTH = "2025-06"
AGENT_CHAT_TIMEOUT = 60.0


def _post_agent_chat(
    http_client: httpx.Client,
    message: str,
    *,
    image_data_url: str | None = None,
    timeout: float = AGENT_CHAT_TIMEOUT,
) -> str:
    payload: dict[str, Any] = {"message": message}
    if image_data_url is not None:
        payload["image_data_url"] = image_data_url
    response = http_client.post("/agent/chat", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()["reply"]


def test_agent_chat_add_transaction(
    http_client: httpx.Client,
    category: dict[str, Any],
    unique_suffix: str,
    require_llm: None,
) -> None:
    merchant = f"集成测试-{unique_suffix}"
    month = datetime.now().strftime("%Y-%m")

    response = _post_agent_chat(
        http_client,
        f"刚才在{merchant}花了12.5块，算{category['name']}",
    )
    assert response

    list_response = http_client.get("/transactions", params={"month": month}, timeout=15.0)
    list_response.raise_for_status()
    created = [
        row
        for row in list_response.json()
        if row.get("merchant") == merchant and float(row["amount"]) == 12.5
    ]
    assert created, f"未找到 Agent 创建的交易（merchant={merchant}）"
    for row in created:
        http_client.delete(f"/transactions/{row['id']}")


def test_agent_chat_query_transactions(
    http_client: httpx.Client,
    transaction: dict[str, Any],
    category: dict[str, Any],
    require_llm: None,
) -> None:
    reply = _post_agent_chat(
        http_client,
        (
            f"查一下{TEST_MONTH}月份分类「{category['name']}」的消费记录，"
            f"有没有商户「{transaction['merchant']}」"
        ),
    )
    assert reply
    assert (
        str(transaction["merchant"]) in reply
        or "38" in reply
        or category["name"] in reply
    )


def test_agent_chat_daily_spending(
    http_client: httpx.Client,
    category: dict[str, Any],
    unique_suffix: str,
    require_llm: None,
) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    merchant = f"日汇总-{unique_suffix}"
    create = http_client.post(
        "/transactions",
        json={
            "amount": 7.9,
            "category": category["name"],
            "merchant": merchant,
            "note": "今日测试",
            "transacted_at": f"{today}T10:00:00",
        },
    )
    create.raise_for_status()
    txn_id = create.json()["id"]

    try:
        reply = _post_agent_chat(http_client, "我今天用了多少钱")
        assert reply
        assert "今天" in reply or "今日" in reply or today in reply
        assert "7.9" in reply or "7.90" in reply
    finally:
        http_client.delete(f"/transactions/{txn_id}")


def test_agent_chat_out_of_scope(
    http_client: httpx.Client,
    require_llm: None,
) -> None:
    reply = _post_agent_chat(http_client, "今天天气怎么样")
    assert reply
    assert "账单" in reply or "记账" in reply
