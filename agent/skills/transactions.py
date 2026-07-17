"""交易 skill — 记一笔、按时间范围查询明细。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from langchain_core.runnables import RunnableConfig
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from server.model.request.transaction import TransactionListQueryRequest
from server.model.transaction import Transaction
from agent.common.skill_category import register_skill_category
from agent.common.skill_policy import account_id_from_config
from agent.skills.common import tool_register
from storage.rag.transaction import transaction_rag
from common.format import format_db_error, format_tool_result
from storage.postgres import transaction_service
from utils.date_range import bounds_from_period
from agent.common.skill_category import SkillCategoryTransaction

# 注册交易分类
register_skill_category(
    SkillCategoryTransaction,
    description="账单记账与查询：记一笔、查汇总、查明细、语义搜消费、CSV/图片导入",
    keywords=(
        "记一笔",
        "记一下",
        "花了多少",
        "汇总",
        "明细",
        "查询",
        "交易",
        "导入",
        "CSV",
        "csv",
        "截图",
        "语义",
        "搜索",
        "收入",
        "支出",
        "工资",
        "入账",
        "记账",
        "收到",
        "列出",
        "最接近",
        "相似",
        "有关",
        "相关",
        "上传",
        "账单文件",
        "识别",
        "预算",
        "图片",
        "花了",
        "消费",
        "总额",
        "本周",
        "明细",
    ),
    patterns=(
        r".*花了\s*\d.*",
        r".*收入\s*\d.*",
        r".*记.*笔.*",
        r".*\d+\s*元.*",
        r".*本月.*多少.*",
        r".*今天.*多少.*",
        r".*昨天.*多少.*",
        r".*今天用了.*",
        r".*最接近.*",
        r".*列出.*交易.*",
        r".*预算.*多少.*",
        r".*支出汇总.*",
        r".*和.+有关.*",
        r".*语义搜索.*",
        r".*找.*消费.*",
        r".*导入.*csv.*",
        r".*上传.*文件.*",
        r".*支付截图.*",
    ),
)


@tool_register(scope="记一笔", skill_category=SkillCategoryTransaction)
async def add_transaction(
    db: AsyncSession,
    amount: float,
    category: str,
    merchant: str = "",
    note: str = "",
    *,
    config: RunnableConfig,
) -> str:
    """记一笔支出或收入.

    Args:
        amount: 金额, 正数.
        category: 分类名, 如 "餐饮", "交通", "工资".
        merchant: 商户或来源, 如 Starbucks, 地铁; 未知可传空字符串.
        note: 补充说明, 没有可传空字符串.
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
        await transaction_rag.produce([created])
        return format_tool_result(created)
    except (IntegrityError, SQLAlchemyError) as exc:
        return format_db_error(exc)


@tool_register(
    scope="查最接近金额的交易",
    skill_category="transaction",
    time_scope="day",
    user_triggers=("最接近", "最近", "哪一笔"),
    time_param="date",
    forbid_tools=("get_summary", "query_transactions"),
    example_queries=("今天最接近20块的是哪一笔",),
    example_note="查 {today_date} 与目标金额最接近的单笔, 不是查总支出",
)
async def find_closest_transaction(
    db: AsyncSession,
    date: str,
    target_amount: float,
    *,
    config: RunnableConfig,
) -> str:
    """查找指定日期内与目标金额最接近的单笔交易, 并附带金额上下邻近各一笔.

    返回 below(<N) / equal(=N) / above(>N) 最多三条, 以及 overall closest.
    用于 "今天哪笔最接近 X 元"; 不要用于查总支出或列全部明细.

    Args:
        date: 日期, 格式 YYYY-MM-DD, 如 2026-06-26.
        target_amount: 目标金额(元), 如 20 表示 20 元.
    """
    account_id = account_id_from_config(config)
    try:
        result = await transaction_service.get_closest_amount_neighbors(
            db,
            account_id=account_id,
            date=date,
            target_amount=Decimal(str(target_amount)),
        )
        if result.closest() is None:
            return format_tool_result({"message": f"{date} 无交易记录"})
        return format_tool_result(result.as_payload())
    except SQLAlchemyError as exc:
        return format_db_error(exc)


@tool_register(
    scope="查交易记录列表",
    skill_category="transaction",
    time_scope="none",
    forbid_tools=("get_summary",),
    example_queries=("列出本月所有交易明细", "查一下今天餐饮消费记录"),
    example_note="明细列表用 query_transactions; 总支出用 get_summary",
)
async def query_transactions(
    db: AsyncSession,
    period: Literal["hour", "day", "week", "month", "year"],
    start: str,
    end: str,
    category: str | None = None,
    *,
    config: RunnableConfig,
) -> str:
    """查询交易明细列表, 指定时间范围内的, 可选按分类过滤. 不要用于查总支出.

    period 表粒度: hour=某整点, day=自然日, week=锚点所在 ISO 周(周一~周日),
    month=自然月, year=自然年. start 为锚点, 闭区间由 period 自动换算.
    例: 本月明细->period=month, start=2026-07; 今天明细->period=day, start=2026-07-04.

    Args:
        period: hour / day / week / month / year.
        start: 锚点, YYYY-MM-DD / YYYY-MM / ISO datetime.
        end: 保留兼容, 实际区间由 period+start 推算, 可传与 start 相同.
        category: 可选分类名; 传入时仅返回该分类下的记录.
    """
    account_id = account_id_from_config(config)
    start_dt, end_dt = bounds_from_period(period, start)
    try:
        result = await transaction_service.get_list(
            db,
            TransactionListQueryRequest(
                AccountId=account_id,
                TransactedAtStart=start_dt,
                TransactedAtEnd=end_dt,
                Category=category or "",
                Page=0,
                PageSize=10000,
            ),
        )
        if not result.data:
            return format_tool_result({"message": "该时间范围内无交易记录", "period": period})
        return format_tool_result(result.data)
    except SQLAlchemyError as exc:
        return format_db_error(exc)
