"""Agent API HTTP 集成测试（真实 LLM，无 mock）。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

from datetime import datetime
from typing import Any

import httpx

TEST_MONTH = "2025-06"
AGENT_CHAT_TIMEOUT = 60.0


def _post_agent_chat(
    http_client: httpx.Client,
    message: str,
    *,
    image_data_url: str | None = None,
    file_name: str | None = None,
    file_text: str | None = None,
    thread_id: str | None = None,
    timeout: float = AGENT_CHAT_TIMEOUT,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"message": message}
    if image_data_url is not None:
        payload["image_data_url"] = image_data_url
    if file_name is not None:
        payload["file_name"] = file_name
    if file_text is not None:
        payload["file_text"] = file_text
    if thread_id is not None:
        payload["thread_id"] = thread_id
    response = http_client.post("/agent/chat", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _assert_cross_turn_memory_reply(
    http_client: httpx.Client,
    *,
    merchant: str,
    thread_id: str,
    category_name: str,
    txn_id: int,
) -> None:
    try:
        turn2 = _post_agent_chat(
            http_client,
            f"刚才在{merchant}记的那笔，金额是多少？分类是什么？",
            thread_id=thread_id,
        )
        reply = turn2["reply"]
        assert turn2["thread_id"] == thread_id
        assert reply
        assert merchant in reply or "15.5" in reply or "15.50" in reply
        assert category_name in reply
    finally:
        http_client.delete(f"/transactions/{txn_id}")


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
    assert response["reply"]

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
    )["reply"]
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
            "Data": {
                "amount": 7.9,
                "category": category["name"],
                "merchant": merchant,
                "note": "今日测试",
                "transacted_at": f"{today}T10:00:00",
            }
        },
    )
    create.raise_for_status()
    txn_id = create.json()["id"]

    try:
        reply = _post_agent_chat(http_client, "我今天用了多少钱")["reply"]
        assert reply
        assert "今天" in reply or "今日" in reply or today in reply
        assert "7.9" in reply or "7.90" in reply
    finally:
        http_client.delete(f"/transactions/{txn_id}")


def test_agent_chat_out_of_scope(
    http_client: httpx.Client,
    require_llm: None,
) -> None:
    reply = _post_agent_chat(http_client, "帮我写一份个人所得税报税方案")["reply"]
    assert reply
    assert "账单" in reply or "记账" in reply


def test_agent_chat_cross_turn_memory(
    http_client: httpx.Client,
    category: dict[str, Any],
    unique_suffix: str,
    require_llm: None,
    require_graph_backend: None,
) -> None:
    merchant = f"跨轮记忆-{unique_suffix}"
    thread_id = f"test-thread-{unique_suffix}"
    month = datetime.now().strftime("%Y-%m")

    turn1 = _post_agent_chat(
        http_client,
        f"刚才在{merchant}花了15.5块，算{category['name']}",
        thread_id=thread_id,
    )
    assert turn1["reply"]
    assert turn1["thread_id"] == thread_id

    list_response = http_client.get("/transactions", params={"month": month}, timeout=15.0)
    list_response.raise_for_status()
    created = [
        row
        for row in list_response.json()
        if row.get("merchant") == merchant and float(row["amount"]) == 15.5
    ]
    assert created, f"未找到首轮创建的交易（merchant={merchant}）"
    txn_id = created[0]["id"]

    _assert_cross_turn_memory_reply(
        http_client,
        merchant=merchant,
        thread_id=thread_id,
        category_name=category["name"],
        txn_id=txn_id,
    )


def test_agent_chat_csv_file(
    http_client: httpx.Client,
    unique_suffix: str,
    require_llm: None,
) -> None:
    prefix = f"agent-csv-{unique_suffix}"
    csv_text = (
        f"在 {prefix}Starbucks 买咖啡花了 12.5 元，餐饮\n"
        "今天天气不错\n"
    )
    try:
        response = _post_agent_chat(
            http_client,
            "导入这份 CSV",
            file_name="sample.csv",
            file_text=csv_text,
            timeout=90.0,
        )
        reply = response["reply"]
        assert reply
        assert "记录" in reply or "导入" in reply or "12.5" in reply
    finally:
        month = datetime.now().strftime("%Y-%m")
        list_response = http_client.get("/transactions", params={"month": month}, timeout=15.0)
        if list_response.is_success:
            for row in list_response.json():
                merchant = row.get("merchant") or ""
                note = row.get("note") or ""
                if prefix in merchant or prefix in note:
                    http_client.delete(f"/transactions/{row['id']}")
