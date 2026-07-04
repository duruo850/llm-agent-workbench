"""Transaction 业务服务 - 薄 CRUD + 汇总查询, 入出均为 ORM / 内部 dataclass."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import and_, func, literal, select, true
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql import lateral

from utils.date_range import day_range, month_range
from server.model.request.transaction import TransactionListQueryRequest
from server.model.transaction import Transaction
from storage.postgres.service.enter import transaction_crud


@dataclass
class TransactionList:
    data: list[Transaction]
    total_count: int


@dataclass
class SummaryResult:
    start: datetime
    end: datetime
    total_amount: Decimal
    total_count: int


@dataclass
class ClosestAmountNeighbors:
    """目标金额邻近的三档候选: 小于 / 等于 / 大于."""

    target_amount: Decimal
    below: Transaction | None
    equal: Transaction | None
    above: Transaction | None

    def closest(self) -> Transaction | None:
        if candidates := [t for t in (self.below, self.equal, self.above) if t is not None]:
            return min(
                candidates,
                key=lambda t: (abs(t.amount - self.target_amount), t.amount),
            )
        else:
            return None

    def as_payload(self) -> dict[str, object]:
        def row(txn: Transaction | None) -> dict[str, object] | None:
            return txn.model_dump(mode="json") if txn else None

        return {
            "target_amount": str(self.target_amount),
            "below": row(self.below),
            "equal": row(self.equal),
            "above": row(self.above),
            "closest": row(self.closest()),
        }


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
        if req.TransactedAtStart is not None and req.TransactedAtEnd is not None:
            filters["transacted_at__gte"] = req.TransactedAtStart
            filters["transacted_at__lte"] = req.TransactedAtEnd
        elif req.Month:
            start, end = month_range(req.Month)
            filters["transacted_at__gte"] = start
            filters["transacted_at__lt"] = end
        elif req.Date:
            start, end = day_range(req.Date)
            filters["transacted_at__gte"] = start
            filters["transacted_at__lt"] = end
        if req.Category:
            filters["category"] = req.Category
        result = await transaction_crud.get_multi(
            db,
            **filters,
            offset=req.Page * req.PageSize,
            limit=req.PageSize,
            sort_columns="transacted_at",
            sort_orders="desc",
            schema_to_select=Transaction,
            return_as_model=True,
        )
        return TransactionList(data=result["data"], total_count=result["total_count"])

    async def get_closest_amount_neighbors(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        date: str,
        target_amount: Decimal,
    ) -> ClosestAmountNeighbors:
        """指定自然日内, 各取一笔 ``amount < N`` / ``= N`` / ``> N`` 的邻近记录."""
        start, end = day_range(date)
        base = and_(
            Transaction.account_id == account_id,
            Transaction.transacted_at >= start,
            Transaction.transacted_at < end,
        )

        def neighbor_lateral(amount_cond: object, *order_by: object):
            return lateral(
                select(Transaction)
                .where(base, amount_cond)
                .order_by(*order_by)
                .limit(1)
            ).alias()

        below_lat = neighbor_lateral(
            Transaction.amount < target_amount,
            Transaction.amount.desc(),
        )
        equal_lat = neighbor_lateral(
            Transaction.amount == target_amount,
            Transaction.transacted_at.desc(),
        )
        above_lat = neighbor_lateral(
            Transaction.amount > target_amount,
            Transaction.amount.asc(),
        )
        Below = aliased(Transaction, below_lat)
        Equal = aliased(Transaction, equal_lat)
        Above = aliased(Transaction, above_lat)
        anchor = select(literal(1).label("_anchor")).subquery()

        stmt = (
            select(Below, Equal, Above)
            .select_from(anchor)
            .outerjoin(below_lat, true())
            .outerjoin(equal_lat, true())
            .outerjoin(above_lat, true())
        )
        row = (await db.execute(stmt)).one()
        below, equal, above = row

        return ClosestAmountNeighbors(
            target_amount=target_amount,
            below=below,
            equal=equal,
            above=above,
        )

    async def get_summary(
        self,
        db: AsyncSession,
        *,
        account_id: int,
        start: datetime,
        end: datetime,
    ) -> SummaryResult:
        """按闭区间 ``[start, end]`` SQL 聚合总支出与笔数."""
        stmt = (
            select(
                func.coalesce(func.sum(Transaction.amount), 0).label("total_amount"),
                func.count().label("total_count"),
            )
            .where(
                Transaction.account_id == account_id,
                Transaction.transacted_at >= start,
                Transaction.transacted_at <= end,
            )
        )
        row = (await db.execute(stmt)).one()
        return SummaryResult(
            start=start,
            end=end,
            total_amount=row.total_amount or Decimal("0"),
            total_count=int(row.total_count),
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
