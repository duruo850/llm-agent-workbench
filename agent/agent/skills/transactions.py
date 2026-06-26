"""交易 skill — 记一笔、按月查询明细。"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent.promt.policy import tool_policy
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
    scope="查最接近金额的交易",
    time_scope="day",
    user_triggers=("最接近", "最近", "哪一笔"),
    time_param="date",
    forbid_tools=("get_daily_summary", "get_monthly_summary", "query_transactions"),
    example_queries=("今天最接近20块的是哪一笔",),
    example_note="查 {today_date} 与目标金额最接近的单笔，不是查总支出",
)
async def find_closest_transaction(
    db: AsyncSession, date: str, target_amount: float
) -> str:
    """查找指定日期内与目标金额最接近的单笔交易。用于「今天哪笔最接近 X 元」；不要用于查总支出或列全部明细。

    Args:
        date: 日期，格式 YYYY-MM-DD，如 2026-06-26。
        target_amount: 目标金额（元），如 20 表示 20 元。
    """
    try:
        row = await transaction_service.find_closest_transaction(
            db, date=date, target_amount=target_amount
        )
        if row is None:
            return format_tool_result({"message": f"{date} 无交易记录"})
        return format_tool_result(row)
    except SQLAlchemyError as exc:
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
