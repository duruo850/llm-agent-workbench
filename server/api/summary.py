"""月度汇总 API。

按分类聚合交易金额与笔数，并与当月预算对比，标记是否超支。
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from utils.date_range import month_range
from server.model.budget import Budget
from server.model.category import Category
from server.model.transaction import Transaction
from server.db.session import get_db
from server.model.request import MonthlySummaryQueryRequest
from server.model.response import CategorySummaryResponse, MonthlySummaryResponse

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/monthly", response_model=MonthlySummaryResponse)
async def monthly_summary(
    query: Annotated[MonthlySummaryQueryRequest, Depends()],
    db: AsyncSession = Depends(get_db),
) -> MonthlySummaryResponse:
    month = query.month
    start, end = month_range(month)

    # 按 category 字符串分组（M1 未 FK 化，与 budgets 通过分类名对齐）
    txn_stmt = (
        select(
            Transaction.category,
            func.sum(Transaction.amount).label("total_amount"),
            func.count().label("transaction_count"),
        )
        .where(
            Transaction.transacted_at >= start,
            Transaction.transacted_at < end,
        )
        .group_by(Transaction.category)
        .order_by(Transaction.category)
    )
    txn_result = await db.execute(txn_stmt)
    txn_rows = txn_result.all()

    # 当月各分类预算上限（category.name ↔ transaction.category）
    budget_stmt = (
        select(Category.name, Budget.limit_amount)
        .join(Budget, Budget.category_id == Category.id)
        .where(Budget.month == month)
    )
    budget_result = await db.execute(budget_stmt)
    budget_by_category = {name: limit for name, limit in budget_result.all()}

    categories: list[CategorySummaryResponse] = []
    total_amount = Decimal("0")
    total_count = 0

    for category, amount, count in txn_rows:
        amount = amount or Decimal("0")
        count = int(count)
        total_amount += amount
        total_count += count
        limit = budget_by_category.get(category)
        over_budget = None
        if limit is not None:
            over_budget = amount > limit
        categories.append(
            CategorySummaryResponse(
                category=category,
                total_amount=amount,
                transaction_count=count,
                budget_limit=limit,
                over_budget=over_budget,
            )
        )

    return MonthlySummaryResponse(
        month=month,
        categories=categories,
        total_amount=total_amount,
        total_count=total_count,
    )
