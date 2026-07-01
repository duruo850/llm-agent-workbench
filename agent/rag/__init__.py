"""RAG — 知识库与交易语义向量化与检索。"""

from __future__ import annotations

from agent.rag.common import KnowledgeDoc, KnowledgeHit
from agent.rag.knowledge import Knowledge
from agent.rag.transaction import (
    TransactionRagService,
    transaction_rag,
)
from common.milvus import available as milvus_available, embedding_ready
from server.model.transaction import Transaction

# 进程内单例，供 skill / API 共用
rag = Knowledge()

# 模块级便捷别名（避免调用方反复 rag.xxx）
index_knowledge = rag.index
is_rag_ready = embedding_ready
is_txn_search_ready = transaction_rag.is_ready
search = rag.search

__all__ = [
    "Knowledge",
    "KnowledgeDoc",
    "KnowledgeHit",
    "Transaction",
    "TransactionRagService",
    "rag",
    "transaction_rag",
    "index_knowledge",
    "is_rag_ready",
    "is_txn_search_ready",
    "search",
    "milvus_available",
]
