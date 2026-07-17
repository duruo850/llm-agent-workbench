#!/usr/bin/env python3
"""M12 意图识别 CLI Demo — 对比 hybrid 路由 vs 全量 tools 的 bind_tools token 估算。

用法::

    .venv/bin/python3.14 examples/06_intent_demo.py
    .venv/bin/python3.14 examples/06_intent_demo.py "本月餐饮花了多少"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent.common.skill_registry import skill_registry
from agent.intent import intent_manager
from agent.skills import init as init_skills
from agent.mcp import MCP_TOOLS, init as init_mcp
from utils.agent.common.token import estimate_bind_tools_tokens
from server.db.session import Database
from common.env import get_database_url


def _ensure_tools_loaded() -> None:
    if skill_registry.all_tool_names():
        return
    try:
        Database.init(get_database_url())
        init_skills(Database.get().async_session_factory)
        import asyncio

        asyncio.run(init_mcp())
        skill_registry.register_skills(MCP_TOOLS, category_id="mcp_gaode")
    except Exception:
        pass


SAMPLE_MESSAGES = [
    "刚才咖啡花了 28 元",
    "本月餐饮花了多少",
    "找和咖啡有关的消费",
    "基金定投有什么好处",
    "导入这份 CSV",
    "今天天气怎么样",
    "你好，你能做什么",
]


def _tool_count_for_category(category_id: str) -> int:
    if category_id == "fallback_all":
        return len(skill_registry.all_tools())
    if category_id == "general_chat":
        return len(skill_registry.tools_for_category("general_chat"))
    return len(skill_registry.tools_for_category(category_id))  # type: ignore[arg-type]


def main() -> None:
    parser = argparse.ArgumentParser(description="M12 intent routing demo")
    parser.add_argument("messages", nargs="*", help="自定义用户消息")
    parser.add_argument("--method", default="hybrid", choices=["rule", "embedding", "bert", "hybrid"])
    args = parser.parse_args()

    _ensure_tools_loaded()
    intent_manager.init()
    messages = args.messages or SAMPLE_MESSAGES
    all_tools = skill_registry.all_tools()
    full_tokens = estimate_bind_tools_tokens(all_tools)

    print(f"全量 tools: {len(all_tools)} 个, bind_tools 估算 token ≈ {full_tokens}\n")
    print(f"{'消息':<28} {'分类':<20} {'方法':<12} {'工具数':<6} {'节省%'}")
    print("-" * 80)

    for message in messages:
        result = intent_manager.classify(message, method=args.method)  # type: ignore[arg-type]
        tool_count = _tool_count_for_category(result.scene)
        category_tools = intent_manager.resolve_tools(result.scene)  # type: ignore[arg-type]
        scene_tokens = estimate_bind_tools_tokens(category_tools)
        saved = (1 - scene_tokens / full_tokens) * 100 if full_tokens else 0
        print(
            f"{message[:26]:<28} {result.scene:<20} {str(result.method):<12} "
            f"{tool_count:<6} {saved:.0f}%"
        )


if __name__ == "__main__":
    main()
