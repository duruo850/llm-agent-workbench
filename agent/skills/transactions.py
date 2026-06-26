"""交易 skill — 记一笔、按月查询明细。"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from agent.promt.policy import tool_policy
from common.format import format_db_error, format_tool_result
from server.service import transaction_service


@tool_policy(scope="记一笔")
async def add_transaction(
    db: AsyncSession,
    amount: float,
    category: str,
    merchant: str = "",
    note: str = "",
) -> str:
    """记一笔支出或收入。

    Args:
        amount: 金额，正数。
        category: 分类名，如「餐饮」「交通」「工资」。
        merchant: 商户或来源，如 Starbucks、地铁；未知可传空字符串。
        note: 补充说明，没有可传空字符串。
    """
    try:
        result = await transaction_service.create_transaction_from_agent(
            db,
            amount=amount,
            category=category,
            merchant=merchant,
            note=note,
        )
        return format_tool_result(result)
    except (IntegrityError, SQLAlchemyError) as exc:
        return format_db_error(exc)


@tool_policy(
    scope="查交易",
    time_scope="month",
    time_param="month",
)
async def query_transactions(
    db: AsyncSession, month: str, category: str | None = None
) -> str:
    """查询指定月份的交易记录，可选按分类过滤。仅用于「某月」明细，不要用于「今天/今日」。

    Args:
        month: 月份，格式 YYYY-MM，如 2025-06。
        category: 可选分类名；传入时仅返回该分类下的记录。
    """
    try:
        rows = await transaction_service.list_transactions(db, month=month, category=category)
        return format_tool_result(rows)
    except SQLAlchemyError as exc:
        return format_db_error(exc)
