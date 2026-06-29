"""Agent MCP 集成 — 与 ``agent/agent``、``agent/graph`` 并列。"""

from agent.mcp.gaode import AMAP_AUTH_MCP_TOOL_NAMES, AmapMCPClient, GeoWeatherResult, resolve_ip_weather
from langchain_core.tools import BaseTool
import logging

__all__ = [
    "AMAP_AUTH_MCP_TOOL_NAMES",
    "AmapMCPClient",
    "GeoWeatherResult",
    "discover_mcp_tools",
    "resolve_ip_weather",
]

## 聚合所有MCP tools
MCP_TOOLS: list[BaseTool] = []

logger = logging.getLogger("billmind.mcp")

async def init():
    """初始化"""
    await AmapMCPClient.init()
    MCP_TOOLS.clear()
    MCP_TOOLS.extend(AmapMCPClient.SKILL_TOOLS)
