"""Agent API HTTP 集成测试（真实 LLM，无 mock）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

TEST_MONTH = "2025-06"
AGENT_CHAT_TIMEOUT = 60.0


def test_agent_chat_add_transaction(
    http_client: httpx.Client,
    category: dict[str, Any],
    unique_suffix: str,
    require_llm: None,
) -> None:
    merchant = f"集成测试-{unique_suffix}"
    month = datetime.now().strftime("%Y-%m")

    response = http_client.post(
        "/agent/chat",
        json={"message": f"刚才在{merchant}花了12.5块，算{category['name']}"},
        timeout=AGENT_CHAT_TIMEOUT,
    )
    response.raise_for_status()
    assert response.json()["reply"]

    list_response = http_client.get("/transactions", params={"month": month}, timeout=15.0)
    list_response.raise_for_status()
    print(list_response.json())
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
    response = http_client.post(
        "/agent/chat",
        json={
            "message": (
                f"查一下{TEST_MONTH}月份分类「{category['name']}」的消费记录，"
                f"有没有商户「{transaction['merchant']}」"
            )
        },
        timeout=AGENT_CHAT_TIMEOUT,
    )
    response.raise_for_status()
    reply = response.json()["reply"]
    print(reply)
    assert reply
    assert (
        str(transaction["merchant"]) in reply
        or "38" in reply
        or category["name"] in reply
    )
