"""BillMind 交易语义搜索 — PG 交易 → Ollama Embedding → Milvus 检索。

门面 ``TransactionRagService``（单例 ``transaction_rag``）提供向量层增删改查；
CLI：``python -m storage.rag.transaction --account-id 1 [--force]``。

增量索引采用生产者-消费者：``produce`` 异步入队，后台线程 ``consume`` 写入 Milvus。
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import queue
import threading
from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

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
from server.model.request.transaction import TransactionListQueryRequest
from storage.postgres import transaction_service
from storage.rag.common import RagBaseService

logger = logging.getLogger("billmind.transaction_rag")


class TransactionRagService(RagBaseService):
    """交易向量服务 — Milvus 集合 ``billmind_transactions`` 增删改查。"""

    COLLECTION_NAME = "billmind_transactions"

    def __init__(self) -> None:
        super().__init__()
        self._tasks: queue.Queue[list[Transaction]] = queue.Queue()
        self._consumer = threading.Thread(
            target=self._consume_loop,
            name="transaction-rag-consumer",
            daemon=True,
        )
        self._consumer.start()

    def _consume_loop(self) -> None:
        while True:
            try:
                self.consume()
            except Exception as exc:
                logger.warning("交易向量 consume 循环异常: %s", exc)

    def consume(self) -> None:
        """从队列取一批交易并同步写入 Milvus（消费者线程调用）。"""
        txns = self._tasks.get()
        try:
            if not txns or not self.is_ready():
                return
            try:
                docs = [txn.to_document() for txn in txns]
                ids = [txn.doc_id() for txn in txns]
                self.add_documents(self.COLLECTION_NAME, docs, ids=ids)
            except Exception as exc:
                logger.warning("交易向量写入失败: %s", exc)
        finally:
            self._tasks.task_done()

    async def produce(self, txns: Sequence[Transaction]) -> None:
        """生产者 — 仅入队，不等待 embedding / Milvus 完成。"""
        if not is_txn_search_incremental_enabled() or not txns:
            return
        if not self.is_ready():
            return
        self._tasks.put(list(txns))

    async def index(
        self,
        db: AsyncSession,
        account_id: int,
        *,
        force: bool = False,
    ) -> int:
        """从 PG 全量同步账号交易到 Milvus。"""
        result = await transaction_service.get_list(
            db,
            TransactionListQueryRequest(AccountId=account_id, Page=0, PageSize=100000),
        )
        rows = result.data
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

        await self.produce(rows)
        self._tasks.join()
        return len(rows)

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
