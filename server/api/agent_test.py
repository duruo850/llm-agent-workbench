"""Agent API 与 db_tools 集成测试。"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from langchain_core.messages import AIMessage

from agent.tools.db_tools import get_db_tools
from server.db.session import async_session_factory
from utils.map_by_name import map_by_name

TEST_MONTH = "2025-06"


def test_agent_chat_health(http_client: httpx.Client) -> None:
    """路由存在；空 message 返回 422。"""
    response = http_client.post("/agent/chat", json={"message": ""})
    assert response.status_code == 422


def test_agent_tools_add_transaction(
    http_client: httpx.Client,
    category: dict[str, Any],
) -> None:
    async def _run() -> None:
        async with async_session_factory() as db:
            tools = map_by_name(get_db_tools(db))
            result = await tools["add_transaction"].ainvoke(
                {
                    "amount": 12.5,
                    "category": category["name"],
                    "merchant": "工具测试",
                    "note": "direct tool test",
                }
            )
            data = json.loads(result)
            assert data["category"] == category["name"]
            assert float(data["amount"]) == 12.5
            http_client.delete(f"/transactions/{data['id']}")

    asyncio.run(_run())


def test_agent_tools_query_and_summary(
    http_client: httpx.Client,
    transaction: dict[str, Any],
    category: dict[str, Any],
) -> None:
    async def _run() -> None:
        async with async_session_factory() as db:
            tools = map_by_name(get_db_tools(db))
            query_result = await tools["query_transactions"].ainvoke(
                {"month": TEST_MONTH, "category": category["name"]}
            )
            rows = json.loads(query_result)
            assert isinstance(rows, list)
            assert any(row["id"] == transaction["id"] for row in rows)

            summary_result = await tools["get_monthly_summary"].ainvoke({"month": TEST_MONTH})
            summary = json.loads(summary_result)
            assert summary["month"] == TEST_MONTH
            assert summary["total_count"] >= 1

    asyncio.run(_run())


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
