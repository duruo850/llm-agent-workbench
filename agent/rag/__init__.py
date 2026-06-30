"""RAG — 知识库向量化与检索。"""

from __future__ import annotations

from agent.rag.rag import KnowledgeDoc, KnowledgeHit, RAG

# 进程内单例，供 skill / API 共用
rag = RAG()

# 模块级便捷别名（避免调用方反复 rag.xxx）
index_knowledge = rag.index
is_rag_ready = rag.is_ready
search = rag.search
milvus_available = rag.available

__all__ = [
    "RAG",
    "KnowledgeDoc",
    "KnowledgeHit",
    "rag",
    "index_knowledge",
    "is_rag_ready",
    "search",
    "milvus_available",
]
