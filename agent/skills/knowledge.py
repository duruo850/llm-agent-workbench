"""知识库 RAG skill — 检索理财文档。"""

from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession
from dataclasses import asdict
from agent.agent.promt.policy import tool_policy
from agent.rag import is_rag_ready, search
from common.format import format_tool_result


@tool_policy(scope="知识库检索")
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
        kb: 可选知识库范围：finance（理财）；留空则搜索全部。
    """
    del db, config
    if not is_rag_ready():
        return format_tool_result(
            {"error": True, "detail": "RAG 未就绪（Milvus 或索引不可用）"}
        )

    kb_filter = kb.strip() or None
    try:
        hits = [asdict(hit) for hit in search(query, kb=kb_filter)]
    except ValueError as exc:
        return format_tool_result({"error": True, "detail": str(exc)})

    if not hits:
        return format_tool_result(
            {"message": "未找到相关知识片段", "query": query, "results": []}
        )

    return format_tool_result({"query": query, "results": hits})
