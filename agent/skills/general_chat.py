"""general_chat skill — 闲聊与功能介绍，预置回复、零 LLM token。"""

from __future__ import annotations

import random

from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from agent.common.skill_category import register_skill_category
from agent.skills.common import tool_register
from agent.common.skill_category import SkillCategoryGeneralChat

CANNED_CHAT_REPLIES: tuple[str, ...] = (
    "你好！我是 BillMind 助手，可以帮你记账、查账、查天气和检索理财知识。",
    "你好啊！需要记一笔、查账单，还是了解理财知识？",
    "我是 BillMind AI 记账助手，专注账单管理与理财知识问答。",
    "我可以：记一笔/查账/导入 CSV、检索理财知识库、查询天气与定位。",
    "你好！我能帮你记录消费、查询汇总与明细、导入账单文件，还能解答理财问题。",
    "我是你的记账小助手，记账、查账、知识检索都可以找我。",
    "你好！支持记一笔、查本月花了多少、语义搜消费、导入 CSV 和查天气哦。",
    "BillMind 可以帮你管理账单：记账、查账、导入、理财知识问答与天气查询。",
)

# 注册通用聊天分类
register_skill_category(
    SkillCategoryGeneralChat,
    description="闲聊与功能介绍：你好、你是谁、你能做什么、帮助",
    keywords=(
        "你好",
        "你好啊",
        "您好",
        "你是谁",
        "你叫什么",
        "你能做什么",
        "你能帮我",
        "你能帮我做什么",
        "有哪些功能",
        "帮助",
        "介绍",
        "hello",
        "hi",
    ),
    patterns=(
        r".*你好.*",
        r".*您好.*",
        r".*你是谁.*",
        r".*你能做什么.*",
        r".*有哪些功能.*",
        r"^帮助$",
        r".*介绍.*",
    ),
)


@tool_register(scope="闲聊回复", skill_category=SkillCategoryGeneralChat)
async def reply_general_chat(
    db: AsyncSession,
    *,
    config: RunnableConfig,
) -> str:
    """返回预置闲聊回复，不调用 LLM。"""
    del db, config
    return random.choice(CANNED_CHAT_REPLIES)
