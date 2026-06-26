"""汇总 skill — 按日 / 按月支出汇总。"""

from __future__ import annotations

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from agent.promt.policy import tool_policy
from common.format import format_db_error, format_tool_result
from server.service import transaction_service


@tool_policy(
    scope="查日汇总",
    time_scope="day",
    user_triggers=("今天", "今日", "当天"),
    time_param="date",
    forbid_tools=("get_monthly_summary",),
    example_queries=("我今天用了多少钱",),
    example_note="查今天（{today_date}），不是查本月",
)
async def get_daily_summary(db: AsyncSession, date: str) -> str:
    """获取指定日期的分类汇总、总支出与笔数，用于回答「今天/今日花了多少」。不能查单笔明细，也不能回答「最接近某金额的是哪一笔」。

    Args:
        date: 日期，格式 YYYY-MM-DD，如 2026-06-26。
    """
    try:
        summary = await transaction_service.get_daily_summary(db, date=date)
        return format_tool_result(summary)
    except SQLAlchemyError as exc:
        return format_db_error(exc)


@tool_policy(
    scope="查月汇总",
    time_scope="month",
    time_param="month",
)
async def get_monthly_summary(db: AsyncSession, month: str) -> str:
    """获取指定月份的分类汇总、总支出与笔数，用于回答「本月/这个月花了多少」。不要用于「今天/今日」。

    Args:
        month: 月份，格式 YYYY-MM，如 2025-06。
    """
    try:
        summary = await transaction_service.get_monthly_summary(db, month=month)
        return format_tool_result(summary)
    except SQLAlchemyError as exc:
        return format_db_error(exc)
