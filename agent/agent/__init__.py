"""M2 Function Calling — ``agent.agent.agent.Agent``。"""

from agent.agent.agent import Agent

__all__ = ["Agent"]


async def init():
    """初始化"""
    await Agent.init()