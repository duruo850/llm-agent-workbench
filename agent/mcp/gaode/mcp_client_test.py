"""高德 MCP 客户端集成测试 — 真实连接 mcp.amap.com。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import asyncio

import pytest

from agent.mcp.gaode.geo import resolve_ip_weather
from agent.mcp.gaode.mcp_client import AmapMCPClient
from common.test.public_ip import (
    fetch_current_public_ip,
)


def test_is_configured(require_amap: None) -> None:
    assert AmapMCPClient.is_configured()


def test_init_loads_all_tools(require_amap: None) -> None:
    async def run() -> None:
        await AmapMCPClient.init()
        tools = await AmapMCPClient.get_tools()
        for tool in tools:
            print("============tool,", tool.name)
            print("tool.description,", tool.description)
            print("tool.args,", tool.args)
            print("tool.args_schema,", tool.args_schema)
            print("tool.response_format,", tool.response_format)
        names = {tool.name for tool in tools}
        assert AmapMCPClient.AMAP_AUTH_MCP_TOOL_NAMES <= names, (
            f"缺少所需工具: {AmapMCPClient.AMAP_AUTH_MCP_TOOL_NAMES - names}"
        )
        assert len(tools) >= len(AmapMCPClient.AMAP_AUTH_MCP_TOOL_NAMES)

    asyncio.run(run())


def test_call_tool_rejects_unauthorized(require_amap: None) -> None:
    async def run() -> None:
        await AmapMCPClient.init()
        with pytest.raises(RuntimeError, match="未授权调用"):
            await AmapMCPClient.call_tool("maps_direction_driving", {"origin": "x", "destination": "y"})

    asyncio.run(run())


def test_call_tool_maps_ip_location(require_amap: None) -> None:
    async def run() -> None:
        # 使用当前公网 IP,vpn可能走外网，高德不识别
        ip = fetch_current_public_ip()
        print("current_public_ip,", ip)

        # 写死厦门ip
        ip = '112.48.54.75'

        raw = await AmapMCPClient.call_tool("maps_ip_location", {"ip": ip})
        print("maps_ip_location raw,", raw)

        result = await resolve_ip_weather(ip)
        print("resolve_ip_weather,", result)

        assert result.ip == ip
        assert result.city or result.province, (
            f"未解析到城市/省份: city={result.city!r} province={result.province!r}"
        )
        assert result.adcode, f"未解析到 adcode: {result!r}"
        assert result.weather, f"未解析到天气: {result!r}"

    asyncio.run(run())
