"""高德 MCP 集成测试 fixture — 依赖 .env 中的 AMAP_MAPS_API_KEY。"""

from __future__ import annotations

import os

import pytest

from common.env import load_env


@pytest.fixture
def require_amap() -> None:
    load_env()
    if not os.getenv("AMAP_MAPS_API_KEY", "").strip():
        pytest.skip("未配置 AMAP_MAPS_API_KEY，跳过高德 MCP 测试")
