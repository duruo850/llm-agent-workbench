"""健康检查。"""

from __future__ import annotations

import httpx


def test_health(http_client: httpx.Client) -> None:
    response = http_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
