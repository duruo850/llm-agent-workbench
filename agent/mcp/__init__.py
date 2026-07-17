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

from agent.common.skill_category import register_skill_category
from agent.common.skill_category import SkillCategoryMcpGaode
from agent.common.skill_registry import skill_registry

# 注册高德地图分类
register_skill_category(
    SkillCategoryMcpGaode,
    description="地理位置与天气：我在哪、当前城市、今天天气、气温",
    keywords=("天气", "气温", "下雨", "定位", "在哪", "城市"),
    patterns=(r".*天气.*", r".*我在哪.*", r".*当前.*城市.*"),
)

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


logger = logging.getLogger("billmind.mcp")

async def init():
    """初始化"""
    await AmapMCPClient.init()
    
    # 注册高德地图分类的工具
    skill_registry.register_skills(AmapMCPClient.SKILL_USED_TOOLS, category_id=SkillCategoryMcpGaode)
