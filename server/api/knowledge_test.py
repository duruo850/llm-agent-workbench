"""Knowledge API 集成测试 — GET /knowledge/search。"""

from __future__ import annotations

import httpx


def test_knowledge_search(http_client: httpx.Client, require_rag: None) -> None:
    response = http_client.get(
        "/knowledge/search",
        params={"q": "应急资金", "kb": "finance"},
    )
    response.raise_for_status()
    body = response.json()
    assert body["query"] == "应急资金"
    assert body["results"], "应命中 finance/03_应急资金.md"


def test_knowledge_search_unauthorized(http_client_no_auth: httpx.Client) -> None:
    response = http_client_no_auth.get("/knowledge/search", params={"q": "登录"})
    assert response.status_code == 401
