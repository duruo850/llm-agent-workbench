"""HTTP 集成测试共用辅助（非 fixture）。"""

from __future__ import annotations

from typing import Any

import httpx


def login(client: httpx.Client, name: str) -> dict[str, Any]:
    response = client.post("/accounts/login", json={"name": name})
    response.raise_for_status()
    return response.json()


def login_token(client: httpx.Client, name: str) -> str:
    return login(client, name)["token"]


def bearer_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
