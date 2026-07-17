"""知识库 RAG skill — 检索理财文档。"""

from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import asdict
from agent.common.skill_category import register_skill_category
from agent.skills.common import tool_register
from storage.rag.knowledge import knowledge
from common.format import format_tool_result
from agent.common.skill_category import SkillCategoryRagKnowledge

# 注册知识库分类
register_skill_category(
    SkillCategoryRagKnowledge,
    description="理财知识问答：应急资金、基金定投、保险、个税扣除、预算规划",
    keywords=(
        "基金",
        "保险",
        "应急",
        "理财",
        "扣除",
        "重疾",
        "定投",
        "知识",
        "养老金",
        "意外险",
        "医疗险",
        "个税",
        "应急资金",
        "指数基金",
        "区别",
    ),
    patterns=(r".*什么是.*", r".*有什么好处.*", r".*如何制定.*"),
)


@tool_register(scope="知识库检索", skill_category=SkillCategoryRagKnowledge)
async def search_knowledge(
    db: AsyncSession,
    query: str,
    kb: str = "",
    *,
    config: RunnableConfig,
) -> str:
    """检索 BillMind 理财知识库。

    Args:
        query: 用户问题或检索关键词。
        kb: 可选知识库范围：'finance'（理财）；留空则搜索全部。
    """
    del db, config
    if not knowledge.is_ready():
        return format_tool_result(
            {"error": True, "detail": "RAG 未就绪(Milvus 或索引不可用）"}
        )

    kb_filter = kb.strip() or None
    try:
        hits = [asdict(hit) for hit in knowledge.search(query, kb=kb_filter)]
    except ValueError as exc:
        return format_tool_result({"error": True, "detail": str(exc)})

    if not hits:
        return format_tool_result(
            {"message": "未找到相关知识片段", "query": query, "results": []}
        )

    return format_tool_result({"query": query, "results": hits})
