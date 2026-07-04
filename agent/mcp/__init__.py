"""Agent MCP 集成 — 与 ``agent/agent``、``agent/graph`` 并列。"""

from agent.mcp.gaode import (
    AMAP_AUTH_MCP_TOOL_NAMES,
    AmapMCPClient,
    IpLocationResult,
    WeatherResult,
    format_location_context,
    resolve_ip_location,
    resolve_weather,
)
from langchain_core.tools import BaseTool
import logging

__all__ = [
    "AMAP_AUTH_MCP_TOOL_NAMES",
    "AmapMCPClient",
    "IpLocationResult",
    "WeatherResult",
    "discover_mcp_tools",
    "format_location_context",
    "resolve_ip_location",
    "resolve_weather",
]

## 聚合所有MCP tools
MCP_TOOLS: list[BaseTool] = []

logger = logging.getLogger("billmind.mcp")

async def init():
    """初始化"""
    await AmapMCPClient.init()
    MCP_TOOLS.clear()
    
    # 暂时不绑定给LLM任何的mcp技能，目前用不上
    # MCP_TOOLS.extend(AmapMCPClient.SKILL_USED_TOOLS) # 仅使用2个工具
