"""Transaction 业务服务 — 增删改查、按月列表与月度汇总（按 account 隔离）。"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from utils.date_range import day_range, month_range
from server.model.budget import Budget
from server.model.category import Category
from server.model.request import TransactionCreateRequest, TransactionUpdateRequest
from server.model.response import (
    CategorySummaryResponse,
    DailySummaryResponse,
    MonthlySummaryResponse,
    TransactionCreateResponse,
    TransactionGetResponse,
    TransactionListResponse,
    TransactionUpdateResponse,
)
from server.model.transaction import Transaction
from server.service.enter import transaction_crud


class TransactionService:
    async def create_transaction(
        self,
        db: AsyncSession,
        body: TransactionCreateRequest,
        *,
        account_id: int,
    ) -> TransactionCreateResponse:
        payload = Transaction(**body.model_dump(), account_id=account_id)
        created = await transaction_crud.create(
            db,
            object=payload,
            schema_to_select=TransactionCreateResponse,
            return_as_model=True,
        )
        if created is None:
            raise RuntimeError("create transaction returned None")
        return created

    async def create_transaction_from_agent(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        amount: float,
        category: str,
        merchant: str = "",
        note: str = "",
    ) -> TransactionCreateResponse:
        """Agent 工具入口 — 从 LLM 提取的标量参数构建请求。"""
        body = TransactionCreateRequest(
            amount=Decimal(str(amount)),
            category=category,
            merchant=merchant,
            note=note,
        )
        return await self.create_transaction(db, body, account_id=account_id)

    async def get_transaction(
        self, db: AsyncSession, transaction_id: int, *, account_id: int
    ) -> TransactionGetResponse | None:
        return await transaction_crud.get(
            db,
            id=transaction_id,
            account_id=account_id,
            schema_to_select=TransactionGetResponse,
            return_as_model=True,
            one_or_none=True,
        )

    async def list_transactions(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        month: str | None = None,
        date: str | None = None,
        category: str | None = None,
    ) -> list[TransactionListResponse]:
        stmt = await transaction_crud.select(
            schema_to_select=TransactionListResponse,
            sort_columns="transacted_at",
            sort_orders="desc",
        )
        stmt = stmt.where(Transaction.account_id == account_id)
        if date:
            start, end = day_range(date)
            stmt = stmt.where(
                Transaction.transacted_at >= start,
                Transaction.transacted_at < end,
            )
        elif month:
            start, end = month_range(month)
            stmt = stmt.where(
                Transaction.transacted_at >= start,
                Transaction.transacted_at < end,
            )
        result = await db.execute(stmt)
        rows = [TransactionListResponse.model_validate(row) for row in result.mappings().all()]
        if category:
            rows = [row for row in rows if row.category == category]
        return rows

    async def find_closest_transaction(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        date: str,
        target_amount: float,
    ) -> TransactionListResponse | None:
        """返回指定日期内与目标金额最接近的单笔交易。"""
        rows = await self.list_transactions(
            db, account_id=account_id, date=date
        )
        if not rows:
            return None
        target = Decimal(str(target_amount))
        return min(rows, key=lambda row: abs(row.amount - target))

    async def get_monthly_summary(
        self, db: AsyncSession, *, account_id: int, month: str
    ) -> MonthlySummaryResponse:
        """按月聚合交易，并关联预算对比（无独立 summary 表）。"""
        start, end = month_range(month)

        txn_stmt = (
            select(
                Transaction.category,
                func.sum(Transaction.amount).label("total_amount"),
                func.count().label("transaction_count"),
            )
            .where(
                Transaction.account_id == account_id,
                Transaction.transacted_at >= start,
                Transaction.transacted_at < end,
            )
            .group_by(Transaction.category)
            .order_by(Transaction.category)
        )
        txn_result = await db.execute(txn_stmt)
        txn_rows = txn_result.all()

        budget_stmt = (
            select(Category.name, Budget.limit_amount)
            .join(Budget, Budget.category_id == Category.id)
            .where(
                Category.account_id == account_id,
                Budget.account_id == account_id,
                Budget.month == month,
            )
        )
        budget_result = await db.execute(budget_stmt)
        budget_by_category = {name: limit for name, limit in budget_result.all()}

        categories: list[CategorySummaryResponse] = []
        total_amount = Decimal("0")
        total_count = 0

        for category_name, amount, count in txn_rows:
            amount = amount or Decimal("0")
            count = int(count)
            total_amount += amount
            total_count += count
            limit = budget_by_category.get(category_name)
            over_budget = None
            if limit is not None:
                over_budget = amount > limit
            categories.append(
                CategorySummaryResponse(
                    category=category_name,
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

    async def get_daily_summary(
        self, db: AsyncSession, *, account_id: int, date: str
    ) -> DailySummaryResponse:
        """按日聚合交易。"""
        start, end = day_range(date)

        txn_stmt = (
            select(
                Transaction.category,
                func.sum(Transaction.amount).label("total_amount"),
                func.count().label("transaction_count"),
            )
            .where(
                Transaction.account_id == account_id,
                Transaction.transacted_at >= start,
                Transaction.transacted_at < end,
            )
            .group_by(Transaction.category)
            .order_by(Transaction.category)
        )
        txn_result = await db.execute(txn_stmt)
        txn_rows = txn_result.all()

        categories: list[CategorySummaryResponse] = []
        total_amount = Decimal("0")
        total_count = 0

        for category_name, amount, count in txn_rows:
            amount = amount or Decimal("0")
            count = int(count)
            total_amount += amount
            total_count += count
            categories.append(
                CategorySummaryResponse(
                    category=category_name,
                    total_amount=amount,
                    transaction_count=count,
                )
            )

        return DailySummaryResponse(
            date=date,
            categories=categories,
            total_amount=total_amount,
            total_count=total_count,
        )

    async def update_transaction(
        self,
        db: AsyncSession,
        transaction_id: int,
        body: TransactionUpdateRequest,
        *,
        account_id: int,
    ) -> TransactionUpdateResponse | None:
        return await transaction_crud.update(
            db,
            object=body,
            id=transaction_id,
            account_id=account_id,
            schema_to_select=TransactionUpdateResponse,
            return_as_model=True,
            one_or_none=True,
        )

    async def delete_transaction(
        self, db: AsyncSession, transaction_id: int, *, account_id: int
    ) -> bool:
        existing = await transaction_crud.get(
            db, id=transaction_id, account_id=account_id
        )
        if existing is None:
            return False
        await transaction_crud.delete(db, id=transaction_id, account_id=account_id)
        return True


transaction_service = TransactionService()
