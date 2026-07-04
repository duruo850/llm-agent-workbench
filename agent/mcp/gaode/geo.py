"""高德 MCP 编排 — IP 定位与天气查询分离。"""

from __future__ import annotations

import ast
import json
import logging
from dataclasses import dataclass
from typing import Any

from agent.mcp.gaode.mcp_client import AmapMCPClient

logger = logging.getLogger("billmind.amap.geo")


@dataclass(frozen=True)
class IpLocationResult:
    """``maps_ip_location`` 解析结果。"""

    ip: str
    province: str | None = None
    city: str | None = None
    adcode: str | None = None


@dataclass(frozen=True)
class WeatherResult:
    """``maps_weather`` 解析结果。"""

    adcode: str
    weather: str | None = None
    temperature: str | None = None


def _text_from_mcp_blocks(raw: str) -> str:
    """从 MCP tool 返回的 content block 字符串中提取 JSON 文本。"""
    text = raw.strip()
    if text.startswith("[") and "'type'" in text and "'text'" in text:
        try:
            blocks = ast.literal_eval(text)
            if isinstance(blocks, list):
                for block in blocks:
                    if isinstance(block, dict) and block.get("type") == "text":
                        inner = block.get("text")
                        if isinstance(inner, str) and inner.strip():
                            return inner.strip()
        except (SyntaxError, ValueError):
            pass
    return text


def _parse_tool_payload(raw: str) -> Any:
    text = _text_from_mcp_blocks(raw)
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"text": text}


def _pick_str(data: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _extract_location(payload: Any) -> dict[str, str | None]:
    if isinstance(payload, list) and payload:
        payload = payload[0]
    if not isinstance(payload, dict):
        return {"province": None, "city": None, "adcode": None}

    nested = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if not isinstance(nested, dict):
        nested = payload

    return {
        "province": _pick_str(nested, "province", "prov"),
        "city": _pick_str(nested, "city", "cityname"),
        "adcode": _pick_str(nested, "adcode", "citycode", "adCode"),
    }


def _extract_weather(payload: Any) -> dict[str, str | None]:
    if isinstance(payload, list) and payload:
        payload = payload[0]
    if not isinstance(payload, dict):
        return {"weather": None, "temperature": None}

    forecasts = payload.get("forecasts")
    if isinstance(forecasts, list) and forecasts:
        first = forecasts[0]
        if isinstance(first, dict):
            casts = first.get("casts")
            if isinstance(casts, list) and casts and isinstance(casts[0], dict):
                day = casts[0]
                return {
                    "weather": _pick_str(day, "dayweather", "weather", "text"),
                    "temperature": _pick_str(day, "daytemp", "temperature", "temp"),
                }
            return {
                "weather": _pick_str(first, "weather", "dayweather", "text"),
                "temperature": _pick_str(first, "temperature", "daytemp", "temp"),
            }

    nested = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    if isinstance(nested, dict):
        return {
            "weather": _pick_str(nested, "weather", "dayweather", "text"),
            "temperature": _pick_str(nested, "temperature", "daytemp", "temp"),
        }

    return {"weather": None, "temperature": None}


async def resolve_ip_location(ip: str) -> IpLocationResult:
    """IP → 省/市/adcode。"""
    if not AmapMCPClient.is_configured():
        raise RuntimeError("未配置 AMAP_MAPS_API_KEY")

    location_raw = await AmapMCPClient.call_tool("maps_ip_location", {"ip": ip})
    location_payload = _parse_tool_payload(location_raw)
    location = _extract_location(location_payload)
    adcode = location["adcode"]
    if not adcode:
        logger.warning("maps_ip_location 未返回 adcode: ip=%s raw=%s", ip, location_raw)

    return IpLocationResult(
        ip=ip,
        province=location["province"],
        city=location["city"],
        adcode=adcode,
    )


async def resolve_weather(adcode: str) -> WeatherResult:
    """adcode → 当日天气。"""
    if not AmapMCPClient.is_configured():
        raise RuntimeError("未配置 AMAP_MAPS_API_KEY")

    code = adcode.strip()
    if not code:
        raise ValueError("adcode 不能为空")

    weather_raw = await AmapMCPClient.call_tool("maps_weather", {"city": code})
    weather_payload = _parse_tool_payload(weather_raw)
    weather_info = _extract_weather(weather_payload)

    return WeatherResult(
        adcode=code,
        weather=weather_info["weather"],
        temperature=weather_info["temperature"],
    )


def format_location_context(result: IpLocationResult) -> str:
    """将 IP 定位结果格式化为 Agent 上下文。"""
    location = f"{result.province or ''}{result.city or ''}".strip()
    if not location:
        return ""
    return f"用户所在地：{location}"
