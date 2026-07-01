"""Transaction 向量服务单测 — 不依赖 Milvus。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from server.model.transaction import Transaction


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
