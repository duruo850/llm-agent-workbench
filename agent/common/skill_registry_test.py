"""SkillRegistry 单测。"""

from __future__ import annotations

import sys
from pathlib import Path

import agent.mcp  # noqa: F401 — register mcp_gaode category

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

from agent.common.skill_registry import skill_registry
from agent.mcp import MCP_TOOLS
from agent.skills import init as init_skills
from common.env import get_database_url
from server.db.session import Database


def _init_registry() -> None:
    import asyncio

    from agent.mcp import init as init_mcp

    Database.init(get_database_url())
    init_skills(Database.get().async_session_factory)
    asyncio.run(init_mcp())
    skill_registry.register_skills(MCP_TOOLS, category_id="mcp_gaode")


def test_all_categories_returns_four() -> None:
    _init_registry()
    assert skill_registry.all_categories() == (
        "mcp_gaode",
        "rag_knowledge",
        "transaction",
        "general_chat",
    )


def test_general_chat_tool() -> None:
    _init_registry()
    names = tuple(t.name for t in skill_registry.tools_for_category("general_chat"))
    assert names == ("reply_general_chat",)


def test_transaction_has_seven_tools() -> None:
    _init_registry()
    names = set(skill_registry.category_tool_names("transaction"))
    assert names == {
        "add_transaction",
        "query_transactions",
        "find_closest_transaction",
        "get_summary",
        "search_similar_transactions",
        "import_csv_file",
        "parse_image_file",
    }


def test_mcp_gaode_tools() -> None:
    _init_registry()
    names = set(skill_registry.category_tool_names("mcp_gaode"))
    assert "maps_weather" in names
    assert "maps_ip_location" in names
