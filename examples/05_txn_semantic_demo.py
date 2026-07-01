#!/usr/bin/env python3
"""M8 交易语义搜索 demo — 同步账号交易并检索。

用法::

    docker compose up -d milvus ollama
    .venv/bin/python3.14 -m agent.rag.transaction --account-id 1
    .venv/bin/python3.14 examples/05_txn_semantic_demo.py
    .venv/bin/python3.14 examples/05_txn_semantic_demo.py --query "星巴克"
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agent.rag import transaction_rag
from common.env import get_database_url
from common.milvus import embedding_ready
from server.db.session import Database


async def _sync(account_id: int, *, force: bool) -> int:
    Database.init(get_database_url())
    async with Database.get().async_session_factory() as db:
        return await transaction_rag.index(db, account_id, force=force)


def main() -> None:
    parser = argparse.ArgumentParser(description="BillMind 交易语义搜索 demo")
    parser.add_argument("--account-id", type=int, default=1, help="账号 ID")
    parser.add_argument("--query", default="上次星巴克花了多少", help="检索问题")
    parser.add_argument("--force", action="store_true", help="强制重建该账号向量")
    args = parser.parse_args()

    if not embedding_ready():
        print("交易语义搜索未就绪，请先: docker compose up -d milvus ollama")
        sys.exit(1)

    count = asyncio.run(_sync(args.account_id, force=args.force))
    print(f"synced {count} transactions")

    hits = transaction_rag.search(args.query, account_id=args.account_id)
    if not hits:
        print("无命中（请确认账号有含 Starbucks/咖啡 等记录并已同步索引）")
        sys.exit(0)

    for i, hit in enumerate(hits, 1):
        print(f"\n--- hit {i} #{hit.id} ---")
        print(hit.embedding_text())


if __name__ == "__main__":
    main()
