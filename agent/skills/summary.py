"""汇总 skill — 按 hour/day/week/month/year 支出汇总。"""

from __future__ import annotations

from typing import Literal

from langchain_core.runnables import RunnableConfig
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent.promt.policy import account_id_from_config, tool_policy
from common.format import format_db_error, format_tool_result
from server.model.response import SummaryResponse
from storage.postgres import transaction_service
from utils.date_range import bounds_from_period


@tool_policy(
    scope="查汇总",
    time_scope="none",
    forbid_tools=(
        "query_transactions",
        "find_closest_transaction",
        "search_similar_transactions",
    ),
    example_queries=("我今天用了多少钱", "这个月一共花了多少钱"),
    example_note="day或month+对应start/end",
)
async def get_summary(
    db: AsyncSession,
    period: Literal["hour", "day", "week", "month", "year"],
    start: str,
    end: str,
    *,
    config: RunnableConfig,
) -> str:
    """唯一汇总工具: 时间范围内的总支出与笔数. 非明细/非最接近金额.

    period 表粒度: hour=某整点, day=自然日, week=锚点所在 ISO 周(周一~周日),
    month=自然月, year=自然年. start 为锚点(今天/本月等), 闭区间由 period 自动换算.
    例: 今天->period=day, start=2026-07-04; 本月->period=month, start=2026-07.

    Args:
        period: hour / day / week / month / year.
        start: 锚点, YYYY-MM-DD / YYYY-MM / ISO datetime.
        end: 保留兼容, 实际区间由 period+start 推算, 可传与 start 相同.
    """
    account_id = account_id_from_config(config)
    start_dt, end_dt = bounds_from_period(period, start)

    try:
        summary = await transaction_service.get_summary(
            db,
            account_id=account_id,
            start=start_dt,
            end=end_dt,
        )
        return format_tool_result(
            SummaryResponse(
                period=period,
                start=summary.start,
                end=summary.end,
                total_amount=summary.total_amount,
                total_count=summary.total_count,
            )
        )
    except SQLAlchemyError as exc:
        return format_db_error(exc)
