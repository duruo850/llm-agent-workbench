"""Agent API HTTP 集成测试。"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
from langchain_core.messages import AIMessage

TEST_MONTH = "2025-06"


def test_agent_chat_health(http_client: httpx.Client) -> None:
    """路由存在；空 message 返回 422。"""
    response = http_client.post("/agent/chat", json={"message": ""})
    assert response.status_code == 422


@patch("agent.runner.get_openai_chat_llm")
def test_agent_chat_with_mock_llm(
    mock_get_llm: MagicMock,
    http_client: httpx.Client,
    category: dict[str, Any],
) -> None:
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    bound = MagicMock()
    mock_llm.bind_tools.return_value = bound

    bound.ainvoke = AsyncMock(
        side_effect=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "add_transaction",
                        "args": {
                            "amount": 6,
                            "category": category["name"],
                            "merchant": "地铁",
                            "note": "",
                        },
                        "id": "call_test_1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="已为您记录地铁支出 6 元。"),
        ]
    )

    response = http_client.post(
        "/agent/chat",
        json={"message": "刚才地铁花了6块，交通"},
    )
    response.raise_for_status()
    body = response.json()
    assert body["reply"]
    assert "6" in body["reply"] or "地铁" in body["reply"]

    list_response = http_client.get("/transactions", params={"month": TEST_MONTH})
    list_response.raise_for_status()
    rows = list_response.json()
    created = [row for row in rows if row.get("merchant") == "地铁" and float(row["amount"]) == 6]
    for row in created:
        http_client.delete(f"/transactions/{row['id']}")


@patch("agent.runner.get_openai_chat_llm")
def test_agent_chat_query_and_summary(
    mock_get_llm: MagicMock,
    http_client: httpx.Client,
    transaction: dict[str, Any],
    category: dict[str, Any],
) -> None:
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    bound = MagicMock()
    mock_llm.bind_tools.return_value = bound

    bound.ainvoke = AsyncMock(
        side_effect=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "query_transactions",
                        "args": {"month": TEST_MONTH, "category": category["name"]},
                        "id": "call_query",
                        "type": "tool_call",
                    },
                    {
                        "name": "get_monthly_summary",
                        "args": {"month": TEST_MONTH},
                        "id": "call_summary",
                        "type": "tool_call",
                    },
                ],
            ),
            AIMessage(content="本月查询与汇总已完成。"),
        ]
    )

    response = http_client.post(
        "/agent/chat",
        json={"message": f"查一下{TEST_MONTH} {category['name']} 的消费并汇总"},
    )
    response.raise_for_status()
    assert response.json()["reply"]

    # 工具经 API 注入的 db session 执行，结果写入同一 PostgreSQL
    list_response = http_client.get(
        "/transactions",
        params={"month": TEST_MONTH, "category": category["name"]},
    )
    list_response.raise_for_status()
    rows = list_response.json()
    assert any(row["id"] == transaction["id"] for row in rows)

    summary_response = http_client.get("/summary/monthly", params={"month": TEST_MONTH})
    summary_response.raise_for_status()
    summary = summary_response.json()
    assert summary["month"] == TEST_MONTH
    assert summary["total_count"] >= 1
