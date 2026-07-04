"""TransactionService.get_summary 单元测试 — 闭区间过滤与 SQL 汇总."""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import pytest
from sqlalchemy import delete

from common.env import get_database_url, load_env
from server.db.session import Database
from server.model.category import Category
from server.model.transaction import Transaction
from storage.postgres.service.account import account_service
from server.model.request.transaction import TransactionListQueryRequest
from storage.postgres.service.transaction import transaction_service
from utils.date_range import bounds_from_period


def _db_reachable() -> bool:
    load_env()
    try:
        Database.init(get_database_url())
        return Database.get().engine is not None
    except Exception:
        return False


@pytest.fixture
def require_postgres() -> None:
    if not _db_reachable():
        pytest.skip("PostgreSQL 不可用，跳过 get_summary 集成测试")


def test_get_summary_closed_interval_excludes_outside_range(require_postgres: None) -> None:
    load_env()
    Database.init(get_database_url())

    async def _run() -> None:
        try:
            async with Database.get().async_session_factory() as db_session:
                suffix = uuid.uuid4().hex[:8]
                account = await account_service.login_or_register(db_session, f"summary-{suffix}")
                assert account.id is not None

                category = Category(account_id=account.id, name=f"餐饮-{suffix}")
                db_session.add(category)
                await db_session.flush()

                month = "2099-03"
                start, end = bounds_from_period("month", month)
                db_session.add_all(
                    [
                        Transaction(
                            account_id=account.id,
                            amount=Decimal("50"),
                            category=category.name,
                            transacted_at=datetime(2099, 3, 15, 12, 0, 0),
                        ),
                        Transaction(
                            account_id=account.id,
                            amount=Decimal("99"),
                            category=category.name,
                            transacted_at=datetime(2099, 2, 28, 23, 59, 59),
                        ),
                        Transaction(
                            account_id=account.id,
                            amount=Decimal("88"),
                            category=category.name,
                            transacted_at=datetime(2099, 4, 1, 0, 0, 0),
                        ),
                    ]
                )
                await db_session.flush()

                summary = await transaction_service.get_summary(
                    db_session,
                    account_id=account.id,
                    start=start,
                    end=end,
                )

                assert summary.total_count == 1
                assert summary.total_amount == Decimal("50")

                await db_session.execute(
                    delete(Transaction).where(Transaction.account_id == account.id)
                )
                await db_session.execute(
                    delete(Category).where(Category.account_id == account.id)
                )
                await db_session.commit()
        finally:
            await Database.get().dispose()
            Database.reset()

    asyncio.run(_run())


def test_get_summary_totals(require_postgres: None) -> None:
    load_env()
    Database.init(get_database_url())

    async def _run() -> None:
        try:
            async with Database.get().async_session_factory() as db_session:
                suffix = uuid.uuid4().hex[:8]
                account = await account_service.login_or_register(
                    db_session, f"summary-cat-{suffix}"
                )
                assert account.id is not None

                category = Category(account_id=account.id, name=f"交通-{suffix}")
                db_session.add(category)
                await db_session.flush()

                month = "2099-04"
                start, end = bounds_from_period("month", month)
                db_session.add(
                    Transaction(
                        account_id=account.id,
                        amount=Decimal("120"),
                        category=category.name,
                        transacted_at=datetime(2099, 4, 10, 10, 0, 0),
                    )
                )
                await db_session.flush()

                summary = await transaction_service.get_summary(
                    db_session,
                    account_id=account.id,
                    start=start,
                    end=end,
                )

                assert summary.total_amount == Decimal("120")
                assert summary.total_count == 1

                await db_session.execute(
                    delete(Transaction).where(Transaction.account_id == account.id)
                )
                await db_session.execute(
                    delete(Category).where(Category.account_id == account.id)
                )
                await db_session.commit()
        finally:
            await Database.get().dispose()
            Database.reset()

    asyncio.run(_run())


def test_get_list_range_closed_interval(require_postgres: None) -> None:
    load_env()
    Database.init(get_database_url())

    async def _run() -> None:
        try:
            async with Database.get().async_session_factory() as db_session:
                suffix = uuid.uuid4().hex[:8]
                account = await account_service.login_or_register(
                    db_session, f"list-range-{suffix}"
                )
                assert account.id is not None

                category = Category(account_id=account.id, name=f"餐饮-{suffix}")
                db_session.add(category)
                await db_session.flush()

                month = "2099-05"
                start, end = bounds_from_period("month", month)
                db_session.add_all(
                    [
                        Transaction(
                            account_id=account.id,
                            amount=Decimal("30"),
                            category=category.name,
                            transacted_at=datetime(2099, 5, 10, 8, 0, 0),
                        ),
                        Transaction(
                            account_id=account.id,
                            amount=Decimal("40"),
                            category=category.name,
                            transacted_at=datetime(2099, 4, 30, 23, 59, 59),
                        ),
                    ]
                )
                await db_session.flush()

                result = await transaction_service.get_list(
                    db_session,
                    TransactionListQueryRequest(
                        AccountId=account.id,
                        TransactedAtStart=start,
                        TransactedAtEnd=end,
                        Page=0,
                        PageSize=100,
                    ),
                )
                assert result.total_count == 1
                assert result.data[0].amount == Decimal("30")

                filtered = await transaction_service.get_list(
                    db_session,
                    TransactionListQueryRequest(
                        AccountId=account.id,
                        TransactedAtStart=start,
                        TransactedAtEnd=end,
                        Category=category.name,
                        Page=0,
                        PageSize=100,
                    ),
                )
                assert filtered.total_count == 1

                await db_session.execute(
                    delete(Transaction).where(Transaction.account_id == account.id)
                )
                await db_session.execute(
                    delete(Category).where(Category.account_id == account.id)
                )
                await db_session.commit()
        finally:
            await Database.get().dispose()
            Database.reset()

    asyncio.run(_run())


def test_get_closest_amount_neighbors(require_postgres: None) -> None:
    load_env()
    Database.init(get_database_url())

    async def _run() -> None:
        try:
            async with Database.get().async_session_factory() as db_session:
                suffix = uuid.uuid4().hex[:8]
                account = await account_service.login_or_register(
                    db_session, f"closest-{suffix}"
                )
                assert account.id is not None

                category = Category(account_id=account.id, name=f"餐饮-{suffix}")
                db_session.add(category)
                await db_session.flush()

                day = "2099-06-15"
                when = datetime(2099, 6, 15, 12, 0, 0)
                db_session.add_all(
                    [
                        Transaction(
                            account_id=account.id,
                            amount=Decimal("10"),
                            category=category.name,
                            transacted_at=when,
                        ),
                        Transaction(
                            account_id=account.id,
                            amount=Decimal("20"),
                            category=category.name,
                            merchant="exact-match",
                            transacted_at=when,
                        ),
                        Transaction(
                            account_id=account.id,
                            amount=Decimal("25"),
                            category=category.name,
                            transacted_at=when,
                        ),
                        Transaction(
                            account_id=account.id,
                            amount=Decimal("99"),
                            category=category.name,
                            transacted_at=datetime(2099, 6, 14, 23, 59, 59),
                        ),
                    ]
                )
                await db_session.flush()

                result = await transaction_service.get_closest_amount_neighbors(
                    db_session,
                    account_id=account.id,
                    date=day,
                    target_amount=Decimal("20"),
                )
                assert result.below is not None and result.below.amount == Decimal("10")
                assert result.equal is not None and result.equal.amount == Decimal("20")
                assert result.above is not None and result.above.amount == Decimal("25")
                assert result.closest() is not None and result.closest().amount == Decimal("20")

                payload = result.as_payload()
                assert payload["below"] is not None
                assert payload["equal"]["merchant"] == "exact-match"
                assert payload["above"] is not None
                assert payload["closest"]["amount"] == "20.00"

                off_day = await transaction_service.get_closest_amount_neighbors(
                    db_session,
                    account_id=account.id,
                    date=day,
                    target_amount=Decimal("22"),
                )
                assert off_day.equal is None
                assert off_day.closest() is not None and off_day.closest().amount == Decimal("20")

                await db_session.execute(
                    delete(Transaction).where(Transaction.account_id == account.id)
                )
                await db_session.execute(
                    delete(Category).where(Category.account_id == account.id)
                )
                await db_session.commit()
        finally:
            await Database.get().dispose()
            Database.reset()

    asyncio.run(_run())
