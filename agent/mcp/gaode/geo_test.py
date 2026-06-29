"""IP 定位 + 天气编排集成测试 — resolve_ip_weather。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import asyncio

from agent.mcp.gaode.geo import resolve_ip_weather
from common.test.public_ip import fetch_current_public_ip


def test_resolve_ip_weather(require_amap: None) -> None:
    async def run() -> None:
        # 使用当前公网 IP,vpn可能走外网，高德不识别
        ip = fetch_current_public_ip()

        # 写死厦门ip
        ip = '112.48.54.75'
        print("current_public_ip,", ip)
        result = await resolve_ip_weather(ip)
        print("result,", result)
        assert result.ip == ip
        assert result.city or result.province, (
            f"未解析到城市/省份: city={result.city!r} province={result.province!r}"
        )
        assert result.adcode, f"未解析到 adcode: {result!r}"
        assert result.weather, f"未解析到天气: {result!r}"

    asyncio.run(run())
