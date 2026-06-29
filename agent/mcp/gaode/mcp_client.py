"""高德 MCP 客户端 — Streamable HTTP 连接，供 REST API 与 Agent 共用。"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from common.env import get_amap_api_key


class AmapMCPClient:
    """高德 MCP 单例 — 懒加载 tools，无 Key 时返回空列表。"""

    logger = logging.getLogger("billmind.amap.mcp")
    AMAP_AUTH_MCP_TOOL_NAMES = frozenset({"maps_ip_location", "maps_weather"})  # 授权的工具

    _client: MultiServerMCPClient | None = None
    _initialized: bool = False
    SKILL_TOOLS: list[BaseTool] = []

    @classmethod
    async def init(cls):
        """连接高德 MCP Server 并缓存全部工具。"""
        if cls._initialized:
            return

        cls._initialized = True
        api_key = get_amap_api_key()
        if not api_key:
            cls.logger.warning("未配置 AMAP_MAPS_API_KEY,跳过高德 MCP 初始化")
            return

        cls._client = MultiServerMCPClient(
            {
                "amap": {
                    "transport": "streamable_http",
                    "url": f"https://mcp.amap.com/mcp?key={api_key}",
                }
            }
        )
        cls.SKILL_TOOLS = await cls._client.get_tools()

    @classmethod
    async def get_tools(cls) -> list[BaseTool]:
        """返回 MCP Server 提供的全部 LangChain 工具（无 Key 时为空）。"""
        if not cls._initialized:
            await cls.init()
        return list(cls.SKILL_TOOLS or [])

    @classmethod
    async def call_tool(cls, name: str, args: dict[str, Any]) -> str:
        """直接调用 MCP tool，供 geo 编排使用；仅允许 AMAP_AUTH_MCP_TOOL_NAMES"""
        if name not in cls.AMAP_AUTH_MCP_TOOL_NAMES:
            raise RuntimeError(f"高德 MCP 工具未授权调用: {name}")
        tools = await cls.get_tools()
        tool = next((item for item in tools if item.name == name), None)
        if tool is None:
            raise RuntimeError(f"高德 MCP 工具不可用: {name}")
        result = await tool.ainvoke(args)
        return result if isinstance(result, str) else str(result)

    @classmethod
    def is_configured(cls) -> bool:
        return bool(get_amap_api_key())
