"""交易语义搜索 skill — 模糊回忆类查账。"""

from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent.promt.policy import account_id_from_config, tool_policy
from storage.rag.transaction import transaction_rag
from common.format import format_tool_result


@tool_policy(
    scope="语义搜历史账单",
    forbid_tools=(
        "get_monthly_summary",
        "get_daily_summary",
        "query_transactions",
        "find_closest_transaction",
    ),
    example_queries=("上次星巴克花了多少", "类似出差住宿的消费"),
    example_note="模糊回忆消费，无明确月份/日期/金额时用；有明确时间或金额则用对应 SQL skill",
)
async def search_similar_transactions(
    db: AsyncSession,
    query: str,
    *,
    config: RunnableConfig,
) -> str:
    """按语义相似度搜索历史交易。用于「上次星巴克花了多少」「类似出差住宿的消费」等模糊回忆；有明确月份/日期/金额时不要使用。

    Args:
        query: 用户描述或关键词，如「星巴克」「出差住宿」。
    """
    # 故意不用db，走的是Milvus向量库
    del db
    account_id = account_id_from_config(config)

    if not transaction_rag.is_ready():
        return format_tool_result(
            {
                "error": True,
                "detail": "交易语义搜索未就绪（Milvus 或 Ollama embedding 不可用）",
            }
        )

    try:
        hits = [
            hit.to_search_dict()
            for hit in transaction_rag.search(query, account_id=account_id)
        ]
    except Exception as exc:
        return format_tool_result({"error": True, "detail": str(exc)})

    if not hits:
        return format_tool_result(
            {
                "message": "未找到相似交易",
                "query": query,
                "hint": "请先运行: python -m storage.rag.transaction --account-id <账号ID>",
                "results": [],
            }
        )

    return format_tool_result({"query": query, "results": hits})
