"""Geo API 集成测试 — GET /geo/me。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import httpx


def test_geo_me_by_ip(http_client: httpx.Client, require_amap: None) -> None:
    # 114.114.114.114 高德已无法解析；用可稳定定位的厦门电信 IP
    test_ip = "112.48.54.75"
    response = http_client.get("/geo/me", params={"ip": test_ip})
    response.raise_for_status()
    body = response.json()
    assert body["ip"] == test_ip
    assert body.get("city") or body.get("province")


def test_geo_me_unauthorized(http_client_no_auth: httpx.Client) -> None:
    response = http_client_no_auth.get("/geo/me", params={"ip": "114.114.114.114"})
    assert response.status_code == 401
