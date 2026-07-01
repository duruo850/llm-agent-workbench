"""交易 skill — 记一笔、按月查询明细。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from langchain_core.runnables import RunnableConfig
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from server.model.request.transaction import TransactionListQueryRequest
from server.model.transaction import Transaction
from agent.agent.promt.policy import account_id_from_config, tool_policy
from storage.rag.transaction import transaction_rag
from common.format import format_db_error, format_tool_result
from storage.postgres import transaction_service


@tool_policy(scope="记一笔")
async def add_transaction(
    db: AsyncSession,
    amount: float,
    category: str,
    merchant: str = "",
    note: str = "",
    *,
    config: RunnableConfig,
) -> str:
    """记一笔支出或收入。

    Args:
        amount: 金额，正数。
        category: 分类名，如「餐饮」「交通」「工资」。
        merchant: 商户或来源，如 Starbucks、地铁；未知可传空字符串。
        note: 补充说明，没有可传空字符串。
    """
    account_id = account_id_from_config(config)
    try:
        created = await transaction_service.create(
            db,
            Transaction(
                account_id=account_id,
                amount=Decimal(str(amount)),
                category=category,
                merchant=merchant,
                note=note,
                transacted_at=datetime.now().replace(microsecond=0),
            ),
        )
        transaction_rag.create([created])
        return format_tool_result(created)
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
    db: AsyncSession,
    date: str,
    target_amount: float,
    *,
    config: RunnableConfig,
) -> str:
    """查找指定日期内与目标金额最接近的单笔交易。用于「今天哪笔最接近 X 元」；不要用于查总支出或列全部明细。

    Args:
        date: 日期，格式 YYYY-MM-DD，如 2026-06-26。
        target_amount: 目标金额（元），如 20 表示 20 元。
    """
    account_id = account_id_from_config(config)
    try:
        result = await transaction_service.get_list(
            db,
            TransactionListQueryRequest(
                AccountId=account_id,
                Date=date,
                Page=0,
                PageSize=10000,
            ),
        )
        if not result.data:
            return format_tool_result({"message": f"{date} 无交易记录"})
        return format_tool_result(result.data)
    except SQLAlchemyError as exc:
        return format_db_error(exc)


@tool_policy(
    scope="查交易",
    time_scope="month",
    time_param="month",
)
async def query_transactions(
    db: AsyncSession,
    month: str,
    category: str | None = None,
    *,
    config: RunnableConfig,
) -> str:
    """查询指定月份的交易记录，可选按分类过滤。仅用于「某月」明细，不要用于「今天/今日」。

    Args:
        month: 月份，格式 YYYY-MM，如 2025-06。
        category: 可选分类名；传入时仅返回该分类下的记录。
    """
    account_id = account_id_from_config(config)
    try:
        result = await transaction_service.get_list(
            db,
            TransactionListQueryRequest(
                AccountId=account_id,
                Month=month,
                Category=category or "",
                Page=0,
                PageSize=10000,
            ),
        )
        return format_tool_result(result.data)
    except SQLAlchemyError as exc:
        return format_db_error(exc)
