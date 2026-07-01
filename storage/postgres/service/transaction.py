"""Transaction 业务服务 - 薄 CRUD + 汇总查询, 入出均为 ORM / 内部 dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from utils.date_range import day_range, month_range
from server.model.budget import Budget
from server.model.category import Category
from server.model.request.transaction import TransactionListQueryRequest
from server.model.transaction import Transaction
from storage.postgres.service.enter import transaction_crud
from sqlalchemy.sql import between


@dataclass
class TransactionList:
    data: list[Transaction]
    total_count: int


@dataclass
class CategorySummaryRow:
    category: str
    total_amount: Decimal
    transaction_count: int
    budget_limit: Decimal | None = None
    over_budget: bool | None = None


@dataclass
class MonthlySummary:
    month: str
    categories: list[CategorySummaryRow]
    total_amount: Decimal
    total_count: int


@dataclass
class DailySummary:
    date: str
    categories: list[CategorySummaryRow]
    total_amount: Decimal
    total_count: int


class TransactionService:
    async def create(self, db: AsyncSession, transaction: Transaction) -> Transaction:
        created = await transaction_crud.create(
            db,
            object=transaction,
            schema_to_select=Transaction,
            return_as_model=True,
        )
        if created is None:
            raise RuntimeError("create transaction returned None")
        return created

    async def get_list(
        self,
        db: AsyncSession,
        req: TransactionListQueryRequest,
    ) -> TransactionList:
        filters: dict[str, object] = {}
        if req.AccountId is not None:
            filters["account_id"] = req.AccountId
        if req.Id is not None:
            filters["id"] = req.Id
        if req.Month:
            start, end = month_range(req.Month)
            filters["transacted_at"] = between(start, end)
        if req.Date:
            start, end = day_range(req.Date)
            filters["transacted_at"] = between(start, end)
        if req.Category:
            filters["category"] = req.Category
        if req.Keyword:
            filters["keyword"] = req.Keyword
        result = await transaction_crud.get_multi(
            db,
            **filters,
            offset=req.Page * req.PageSize,
            limit=req.PageSize,
            schema_to_select=Transaction,
            return_as_model=True,
        )
        return TransactionList(data=result.data, total_count=result.total_count)

    async def get_monthly_summary(
        self, db: AsyncSession, *, account_id: int, month: str
    ) -> MonthlySummary:
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
        budget_by_category = dict(budget_result.all())

        categories: list[CategorySummaryRow] = []
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
                CategorySummaryRow(
                    category=category_name,
                    total_amount=amount,
                    transaction_count=count,
                    budget_limit=limit,
                    over_budget=over_budget,
                )
            )

        return MonthlySummary(
            month=month,
            categories=categories,
            total_amount=total_amount,
            total_count=total_count,
        )

    async def get_daily_summary(
        self, db: AsyncSession, *, account_id: int, date: str
    ) -> DailySummary:
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

        categories: list[CategorySummaryRow] = []
        total_amount = Decimal("0")
        total_count = 0

        for category_name, amount, count in txn_rows:
            amount = amount or Decimal("0")
            count = int(count)
            total_amount += amount
            total_count += count
            categories.append(
                CategorySummaryRow(
                    category=category_name,
                    total_amount=amount,
                    transaction_count=count,
                )
            )

        return DailySummary(
            date=date,
            categories=categories,
            total_amount=total_amount,
            total_count=total_count,
        )

    async def update(self, db: AsyncSession, transaction: Transaction) -> Transaction | None:
        return await transaction_crud.update(
            db,
            object={
                "amount": transaction.amount,
                "category": transaction.category,
                "merchant": transaction.merchant,
                "note": transaction.note,
                "transacted_at": transaction.transacted_at,
            },
            id=transaction.id,
            account_id=transaction.account_id,
            schema_to_select=Transaction,
            return_as_model=True,
            one_or_none=True,
        )

    async def delete(self, db: AsyncSession, transaction: Transaction) -> None:
        await transaction_crud.delete(
            db, id=transaction.id, account_id=transaction.account_id
        )


transaction_service = TransactionService()
