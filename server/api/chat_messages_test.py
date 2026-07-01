"""Chat messages API HTTP 集成测试."""

from __future__ import annotations

import httpx


def test_conversation_messages_not_found(http_client: httpx.Client) -> None:
    response = http_client.get("/conversations/nonexistent-thread-id/messages", timeout=15.0)
    assert response.status_code == 404
