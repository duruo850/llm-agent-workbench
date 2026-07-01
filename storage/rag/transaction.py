"""BillMind 交易语义搜索 — PG 交易 → Ollama Embedding → Milvus 检索。

门面 ``TransactionRagService``（单例 ``transaction_rag``）提供向量层增删改查；
CLI：``python -m storage.rag.transaction --account-id 1 [--force]``。
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from common.env import (
    get_database_url,
    get_rag_top_k,
    is_txn_search_incremental_enabled,
    load_env,
)
from common.milvus import available as milvus_available
from common.milvus import get_client
from server.db.session import Database
from server.model.transaction import Transaction
from storage.postgres import transaction_service
from storage.rag.common import RagBaseService

logger = logging.getLogger("billmind.transaction_rag")


class TransactionRagService(RagBaseService):
    """交易向量服务 — Milvus 集合 ``billmind_transactions`` 增删改查。"""

    COLLECTION_NAME = "billmind_transactions"

    def __init__(self) -> None:
        super().__init__()

    def create(self, txns: Sequence[Transaction]) -> List[str]:
        """批量增量索引（受 ``TXN_SEARCH_INCREMENTAL`` 控制）。"""
        if not is_txn_search_incremental_enabled() or not txns:
            return []
        if not self.is_ready():
            return []
        try:
            return self.add_documents(self.COLLECTION_NAME, [txn.to_document() for txn in txns])
        except Exception as exc:
            logger.warning("交易向量 create 失败: %s", exc)
            return []

    async def index(
        self,
        db: AsyncSession,
        account_id: int,
        *,
        force: bool = False,
    ) -> int:
        """
        从 PG 全量同步账号交易到 Milvus。
        """
        rows = await transaction_service.list_transactions(db, account_id=account_id)
        if force:
            if rows:
                self.delete_by_expr(self.COLLECTION_NAME, f"account_id == {account_id}")
            elif milvus_available():
                client = get_client()
                if client.has_collection(self.COLLECTION_NAME):
                    self.delete_by_expr(self.COLLECTION_NAME, f"account_id == {account_id}")
            self.delete_vector_store(self.COLLECTION_NAME)

        if not rows:
            logger.warning("账号 %s 无交易记录，跳过同步", account_id)
            return 0

        if not self.is_ready():
            raise RuntimeError("交易语义搜索未就绪（Milvus 或 Ollama embedding 不可用）")

        return self.create(rows)

    def search(
        self,
        query: str,
        *,
        account_id: int,
        top_k: int | None = None,
    ) -> list[Transaction]:
        """按 account_id 租户隔离的相似度检索。"""
        k = top_k or get_rag_top_k()
        expr = f"account_id == {account_id}"
        docs = self.get_vector_store(self.COLLECTION_NAME).similarity_search(query.strip(), k=k, expr=expr)
        return [Transaction.from_document(doc) for doc in docs]


transaction_rag = TransactionRagService()


def main() -> None:
    """CLI — 全量同步账号交易向量。"""
    load_env()
    parser = argparse.ArgumentParser(description="BillMind 交易语义索引全量同步")
    parser.add_argument("--account-id", type=int, required=True, help="账号 ID")
    parser.add_argument("--force", action="store_true", help="删除该账号已有向量后重建")
    args = parser.parse_args()

    if not milvus_available():
        raise SystemExit("Milvus 不可达，请先: docker compose up -d milvus")
    
    
    async def _cli_sync(account_id: int, *, force: bool) -> int:
        Database.init(get_database_url())
        async with Database.get().async_session_factory() as db:
            return await transaction_rag.index(db, account_id, force=force)

    count = asyncio.run(_cli_sync(args.account_id, force=args.force))
    print(f"synced {count} transactions")


if __name__ == "__main__":
    main()
