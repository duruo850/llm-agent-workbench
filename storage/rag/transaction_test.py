"""Transaction 向量服务单测 — 不依赖 Milvus。"""

from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal

import pytest

from server.model.transaction import Transaction
from storage.rag.transaction import transaction_rag


def _sample_txn(**overrides: object) -> Transaction:
    defaults = {
        "id": 1,
        "account_id": 7,
        "amount": Decimal("38.50"),
        "category": "餐饮",
        "merchant": "Starbucks",
        "note": "拿铁",
        "transacted_at": datetime(2026, 6, 15, 12, 0, 0),
    }
    defaults.update(overrides)
    return Transaction(**defaults)  # type: ignore[arg-type]


def test_embedding_text_format() -> None:
    assert _sample_txn().embedding_text() == "2026-06-15 餐饮 Starbucks 拿铁 38.50元"


def test_embedding_text_empty_merchant_note() -> None:
    txn = _sample_txn(
        id=2,
        amount=Decimal("10"),
        category="交通",
        merchant="",
        note="",
        transacted_at=datetime(2026, 1, 1),
    )
    assert txn.embedding_text() == "2026-01-01 交通   10元"


def test_doc_id_for_milvus_pk() -> None:
    txn = _sample_txn(id=99, account_id=7)
    assert txn.doc_id() == "7_99"


def test_produce_enqueues_for_consumer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "storage.rag.transaction.is_txn_search_incremental_enabled",
        lambda: True,
    )
    monkeypatch.setattr(transaction_rag, "is_ready", lambda: True)
    called: list[list] = []

    def fake_add_documents(
        collection_name: str,
        documents: list,
        *,
        drop_old: bool = False,
        ids: list[str] | None = None,
    ) -> list[str]:
        del collection_name, drop_old
        called.append(documents)
        return ids or []

    monkeypatch.setattr(transaction_rag, "add_documents", fake_add_documents)

    async def _run() -> None:
        await transaction_rag.produce([_sample_txn()])
        transaction_rag._tasks.join()

    asyncio.run(_run())

    assert len(called) == 1
    assert called[0][0].metadata["transaction_id"] == 1


def test_milvus_document_round_trip() -> None:
    txn = _sample_txn()
    restored = Transaction.from_document(txn.to_document(), score=0.9)
    assert restored.id == txn.id
    assert restored.account_id == txn.account_id
    assert restored.category == txn.category
    assert restored.merchant == txn.merchant
    assert restored.note == txn.note
    assert restored.amount == txn.amount
    assert restored.transacted_at == txn.transacted_at
    assert restored.embedding_text() == txn.embedding_text()
    assert restored.search_score == 0.9
