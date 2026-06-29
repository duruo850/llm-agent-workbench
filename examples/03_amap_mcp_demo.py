#!/usr/bin/env python3
"""M6 高德 MCP demo — IP 定位 + 天气（不启动全站）。

用法::

    .venv/bin/python3.14 examples/03_amap_mcp_demo.py
    .venv/bin/python3.14 examples/03_amap_mcp_demo.py --ip 114.114.114.114
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agent.mcp.gaode import AmapMCPClient, resolve_ip_weather
from common.env import get_amap_api_key


async def main() -> None:
    parser = argparse.ArgumentParser(description="高德 MCP IP 定位 + 天气 demo")
    parser.add_argument(
        "--ip",
        default="114.114.114.114",
        help="要查询的 IP（默认 114.114.114.114）",
    )
    args = parser.parse_args()

    if not get_amap_api_key():
        print("请在 .env 中配置 AMAP_MAPS_API_KEY")
        sys.exit(1)

    await AmapMCPClient.init()
    tools = await AmapMCPClient.get_tools()
    print("MCP tools:", ", ".join(tool.name for tool in tools) or "(无)")

    result = await resolve_ip_weather(args.ip)
    print(f"IP: {result.ip}")
    print(f"位置: {result.province or '-'} {result.city or '-'} (adcode={result.adcode or '-'})")
    print(f"天气: {result.weather or '-'} {result.temperature or '-'}°C")


if __name__ == "__main__":
    asyncio.run(main())
