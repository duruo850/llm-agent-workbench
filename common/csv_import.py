"""CSV 逐句导入 — 纯文本拆分与入库编排（LLM 解析由调用方注入）。"""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from storage.rag.transaction import transaction_rag
from server.model.request.parsed import ParsedTransaction
from server.model.transaction import Transaction
from storage.postgres.service import transaction_service


@dataclass
class ImportCategorySummary:
    category: str
    count: int
    total_amount: Decimal


@dataclass
class ImportResult:
    imported_count: int
    skipped_count: int
    errors: list[str]
    categories: list[ImportCategorySummary]


@dataclass
class ParsedSentence:
    """单句解析结果（与 agent.agent.common.parse_sentence.SentenceParseResult 同形）。"""

    is_transaction: bool
    transaction: object | None = None


ParseSentenceFn = Callable[[str], Awaitable[ParsedSentence]]


def _decode_content(content: bytes | str) -> str:
    return content.decode("utf-8-sig") if isinstance(content, bytes) else content


def parse_csv_sentences(content: bytes | str) -> tuple[list[str], list[str]]:
    """从 CSV/纯文本提取非空句子（每行一句；可选首行表头 ``text``）。"""
    text = _decode_content(content).strip()
    if not text:
        return [], ["empty file"]

    sentences: list[str] = []
    for row in csv.reader(io.StringIO(text)):
        if not row or all(not cell.strip() for cell in row):
            continue
        sentence = row[0].strip() if len(row) == 1 else "，".join(
            cell.strip() for cell in row if cell.strip()
        )
        if not sentence:
            continue
        if not sentences and sentence.lower() in {"text", "sentence", "content"}:
            continue
        sentences.append(sentence)

    if not sentences:
        return [], ["no sentences"]
    return sentences, []


def _aggregate_categories(
    imported: list[tuple[str, Decimal]],
) -> list[ImportCategorySummary]:
    totals: dict[str, tuple[int, Decimal]] = defaultdict(lambda: (0, Decimal("0")))
    for category, amount in imported:
        count, total = totals[category]
        totals[category] = (count + 1, total + amount)
    return [
        ImportCategorySummary(category=name, count=count, total_amount=total)
        for name, (count, total) in sorted(totals.items())
    ]


async def import_csv_transactions(
    db: AsyncSession,
    *,
    account_id: int,
    content: bytes | str,
    parse_sentence: ParseSentenceFn,
) -> ImportResult:
    """逐句解析并入库：账单入库，非账单跳过。"""
    sentences, parse_errors = parse_csv_sentences(content)
    errors = list(parse_errors)
    imported_rows: list[tuple[str, Decimal]] = []
    created_transactions: list[Transaction] = []
    skipped_count = 0

    for row_num, sentence in enumerate(sentences, start=1):
        try:
            parsed = await parse_sentence(sentence)
        except Exception as exc:
            skipped_count += 1
            errors.append(f"row {row_num}: parse failed ({exc})")
            continue

        if not parsed.is_transaction or parsed.transaction is None:
            skipped_count += 1
            continue

        try:
            txn = parsed.transaction
            if not isinstance(txn, ParsedTransaction):
                raise TypeError(f"expected ParsedTransaction, got {type(txn).__name__}")
            created = await transaction_service.create(
                db,
                Transaction(
                    account_id=account_id,
                    amount=Decimal(str(txn.amount)),
                    category=txn.category,
                    merchant=txn.merchant,
                    note=txn.note,
                    transacted_at=datetime.now().replace(microsecond=0),
                ),
            )
            imported_rows.append((created.category, created.amount))
            created_transactions.append(created)
        except Exception as exc:
            skipped_count += 1
            errors.append(f"row {row_num}: import failed ({exc})")

    # 将创建的交易向量添加到 Milvus向量库
    transaction_rag.create(created_transactions)
    return ImportResult(
        imported_count=len(imported_rows),
        skipped_count=skipped_count,
        errors=errors,
        categories=_aggregate_categories(imported_rows),
    )
