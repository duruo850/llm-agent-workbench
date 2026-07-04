"""IP 定位 + 天气集成测试。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import asyncio

from agent.mcp.gaode.geo import IpLocationResult, format_location_context, resolve_ip_location, resolve_weather


def test_resolve_ip_location(require_amap: None) -> None:
    async def run() -> None:
        ip = "112.48.54.75"
        result = await resolve_ip_location(ip)
        assert result.ip == ip
        assert result.city or result.province
        assert result.adcode

    asyncio.run(run())


def test_resolve_weather(require_amap: None) -> None:
    async def run() -> None:
        location = await resolve_ip_location("112.48.54.75")
        assert location.adcode
        weather = await resolve_weather(location.adcode)
        assert weather.adcode == location.adcode
        assert weather.weather

    asyncio.run(run())


def test_format_location_context() -> None:
    text = format_location_context(
        IpLocationResult(
            ip="112.48.54.75",
            province="福建省",
            city="厦门市",
            adcode="350200",
        )
    )
    assert text == "用户所在地：福建省厦门市"
