"""CSV 文件 skill — 纯文本逐句解析，不走多模态。"""

from __future__ import annotations

from langchain_core.runnables import RunnableConfig
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent.promt.policy import account_id_from_config, tool_policy
from agent.agent.common.parse_sentence import parse_sentence
from common.csv_import import ImportResult, import_csv_transactions
from common.format import format_db_error, format_tool_result


def _format_import_summary(result: ImportResult) -> dict:
    category_parts = [
        f"{item.category} {item.count} 笔合计 {item.total_amount} 元"
        for item in result.categories
    ]
    message = f"共记录 {result.imported_count} 句话，忽略 {result.skipped_count} 句话"
    if category_parts:
        message += "；" + "；".join(category_parts)
    if result.errors:
        message += f"；{len(result.errors)} 条错误"
    return {
        "message": message,
        "imported_count": result.imported_count,
        "skipped_count": result.skipped_count,
        "errors": result.errors,
        "categories": [
            {
                "category": item.category,
                "count": item.count,
                "total_amount": str(item.total_amount),
            }
            for item in result.categories
        ],
    }


@tool_policy(
    scope="CSV文件导入",
    user_triggers=("CSV", "csv", "流水文件", "账单文件"),
    example_queries=("导入这份 CSV 文件",),
    example_note="用户上传 .csv 文件时使用 import_csv_file，不要用图片识别",
)
async def import_csv_file(
    db: AsyncSession,
    csv_text: str,
    *,
    config: RunnableConfig,
) -> str:
    """导入 CSV 文件中的记账句子（每行一句；是账单则入库，不是则跳过）。

    仅用于 CSV 文本文件，不使用视觉/多模态。

    Args:
        csv_text: CSV 文件全文。
    """
    account_id = account_id_from_config(config)
    try:
        result = await import_csv_transactions(
            db,
            account_id=account_id,
            content=csv_text,
            parse_sentence=parse_sentence,
        )
        return format_tool_result(_format_import_summary(result))
    except SQLAlchemyError as exc:
        return format_db_error(exc)
