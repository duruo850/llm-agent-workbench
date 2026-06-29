"""M4 LangGraph — ``agent.graph.agent.Agent``。"""

from agent.graph.agent import Agent

__all__ = ["Agent"]


async def init():
    """初始化"""
    Agent.init()