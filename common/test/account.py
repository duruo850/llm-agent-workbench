"""HTTP 集成测试共用辅助（非 fixture）。"""

from __future__ import annotations

from typing import Any

import httpx

_DEFAULT_PASSWORD = "test-pass"


def register(
    client: httpx.Client, name: str, password: str = _DEFAULT_PASSWORD
) -> dict[str, Any]:
    response = client.post(
        "/accounts/register",
        json={"name": name, "password": password},
    )
    response.raise_for_status()
    return response.json()


def login(
    client: httpx.Client, name: str, password: str = _DEFAULT_PASSWORD
) -> dict[str, Any]:
    """注册（若已存在忽略）后账号密码登录。"""
    reg = client.post(
        "/accounts/register",
        json={"name": name, "password": password},
    )
    if reg.status_code not in {200, 409}:
        reg.raise_for_status()
    response = client.post(
        "/accounts/login",
        json={"name": name, "password": password},
    )
    response.raise_for_status()
    return response.json()


def bearer_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
