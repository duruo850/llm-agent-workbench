"""Conversations API HTTP 集成测试."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

AGENT_CHAT_TIMEOUT = 60.0


def test_conversations_after_agent_chat(
    http_client: httpx.Client,
    require_llm: None,
    unique_suffix: str,
) -> None:
    thread_id = f"conv-test-{unique_suffix}"
    user_message = f"你好, 这是会话测试 {unique_suffix}"

    chat_response = http_client.post(
        "/agent/chat",
        json={"message": user_message, "thread_id": thread_id},
        timeout=AGENT_CHAT_TIMEOUT,
    )
    chat_response.raise_for_status()
    body = chat_response.json()
    assert body["thread_id"] == thread_id
    assert body["reply"]

    list_response = http_client.get("/conversations", timeout=15.0)
    list_response.raise_for_status()
    conversations: list[dict[str, Any]] = list_response.json()["List"]
    assert any(row["thread_id"] == thread_id for row in conversations)

    messages_response = http_client.get(
        f"/conversations/{thread_id}/messages",
        timeout=15.0,
    )
    messages_response.raise_for_status()
    messages: list[dict[str, Any]] = messages_response.json()["List"]
    roles = {row["role"] for row in messages}
    assert "user" in roles
    assert "assistant" in roles
    assert any(user_message in row["content"] for row in messages if row["role"] == "user")
