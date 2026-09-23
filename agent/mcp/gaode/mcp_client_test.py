"""高德 MCP 客户端集成测试 — 真实连接 mcp.amap.com。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import asyncio

import pytest

from agent.mcp.gaode.geo import resolve_ip_location, resolve_weather
from agent.mcp.gaode.mcp_client import AmapMCPClient
from common.test.public_ip import (
    fetch_current_public_ip,
)


def test_is_configured(require_amap: None) -> None:
    assert AmapMCPClient.is_configured()


def test_init_loads_all_tools(require_amap: None) -> None:
    async def run() -> None:
        await AmapMCPClient.init()
        names = {tool.name for tool in AmapMCPClient.SKILL_USED_TOOLS}
        assert names == set(AmapMCPClient.AMAP_AUTH_MCP_TOOL_NAMES)

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
        ip = "112.48.54.75"

        raw = await AmapMCPClient.call_tool("maps_ip_location", {"ip": ip})
        print("maps_ip_location raw,", raw)

        result = await resolve_ip_location(ip)
        print("resolve_ip_location,", result)

        assert result.ip == ip
        assert result.city or result.province, (
            f"未解析到城市/省份: city={result.city!r} province={result.province!r}"
        )
        assert result.adcode, f"未解析到 adcode: {result!r}"

        weather = await resolve_weather(result.adcode)
        print("resolve_weather,", weather)
        assert weather.weather, f"未解析到天气: {weather!r}"

    asyncio.run(run())


def test_maps_ip_location_trace_remote_ip(require_amap: None) -> None:
    """对照：国内已知 IP vs 线上访客 IP，打印 raw / payload / 解析结果以定位空 adcode。"""
    from agent.mcp.gaode.geo import _extract_location, _parse_tool_payload

    known_china_ip = "112.48.54.75"
    # 线上日志里的访客公网 IP（高德对境外 IP 常返回空）
    remote_visitor_ip = "143.20.38.88"

    async def probe(ip: str) -> dict[str, object]:
        raw = await AmapMCPClient.call_tool("maps_ip_location", {"ip": ip})
        payload = _parse_tool_payload(raw)
        extracted = _extract_location(payload)
        resolved = await resolve_ip_location(ip)
        print("==== maps_ip_location trace ====")
        print("ip:", ip)
        print("raw:", raw)
        print("payload:", payload)
        print("extracted:", extracted)
        print("resolved:", resolved)
        return {
            "ip": ip,
            "raw": raw,
            "payload": payload,
            "extracted": extracted,
            "resolved": resolved,
        }

    async def run() -> None:
        china = await probe(known_china_ip)
        remote = await probe(remote_visitor_ip)

        china_resolved = china["resolved"]
        assert china_resolved.adcode, (
            f"对照 IP {known_china_ip} 也应有 adcode，否则是 Key/MCP/解析链路坏了: {china}"
        )

        remote_resolved = remote["resolved"]
        if not remote_resolved.adcode:
            # 明确区分：不是解析丢字段，而是高德对该 IP 无定位数据
            payload = remote["payload"]
            print(
                "CONCLUSION: 高德对 "
                f"{remote_visitor_ip} 未返回省市/adcode。"
                f" payload={payload!r}"
            )
            assert isinstance(payload, dict)
            # 若 raw 里其实有省市但 extracted 为空 → 解析 bug
            raw_text = str(remote["raw"])
            if any(k in raw_text for k in ("province", "city", "adcode")):
                # 有字段名但值为空列表/空串也常见；仅当出现非空中文省市才算解析漏了
                import re

                if re.search(r"[\u4e00-\u9fff]{2,}", raw_text):
                    raise AssertionError(
                        f"raw 含中文定位信息但解析为空，疑似解析 bug: raw={raw_text}"
                    )

    asyncio.run(run())
