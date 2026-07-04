"""高德 MCP — IP 定位与天气。"""

from agent.mcp.gaode.geo import (
    IpLocationResult,
    WeatherResult,
    format_location_context,
    resolve_ip_location,
    resolve_weather,
)
from agent.mcp.gaode.mcp_client import AmapMCPClient

AMAP_AUTH_MCP_TOOL_NAMES = AmapMCPClient.AMAP_AUTH_MCP_TOOL_NAMES

__all__ = [
    "AMAP_AUTH_MCP_TOOL_NAMES",
    "AmapMCPClient",
    "IpLocationResult",
    "WeatherResult",
    "format_location_context",
    "resolve_ip_location",
    "resolve_weather",
]
