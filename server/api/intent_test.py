"""GET /intent/classify HTTP 集成测试。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import httpx


def test_intent_classify_rule(http_client: httpx.Client) -> None:
    response = http_client.get(
        "/intent/classify",
        params={"q": "刚才咖啡花了 28 元", "method": "rule"},
        timeout=15.0,
    )
    response.raise_for_status()
    body = response.json()
    assert body["scene"] == "transaction"
    assert body["method"] == "rule"
    assert body["confidence"] == 1.0


def test_intent_classify_general_chat(http_client: httpx.Client) -> None:
    response = http_client.get(
        "/intent/classify",
        params={"q": "你好，你能做什么", "method": "rule"},
        timeout=15.0,
    )
    response.raise_for_status()
    assert response.json()["scene"] == "general_chat"
