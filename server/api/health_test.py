"""健康检查 API 集成测试。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import httpx


def test_health(http_client: httpx.Client) -> None:
    response = http_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
