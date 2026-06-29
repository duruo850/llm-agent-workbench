"""BillMind Agent 层 — 默认导出 LangGraph Agent（M4）。"""

from agent.graph import Agent # 导出Agent类，用于在server中使用
from agent.graph import init as init_agent_graph
from agent.skills import init  as init_skills
from agent.mcp import init  as init_mcp
from server.db.session import Database

__all__ = ["Agent"]

async def init_agent():
    """初始化"""
    # 初始化 skills
    init_skills(Database.get().async_session_factory)
    print("skills initialized")
    # 初始化 MCP
    await init_mcp()
    print("mcp initialized")
    # 初始化 Agent
    await init_agent_graph()
    print("agent initialized")