"""BillMind 知识库 RAG — 扫描 Markdown、Ollama 向量化、Milvus 存储与检索。"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from langchain_core.documents import Document
from langchain_milvus import Milvus

from agent.rag.common import get_vector_store
from agent.rag.common import RagBaseService
from agent.rag.common import KnowledgeHit

from common.env import (
    get_rag_top_k,
)

logger = logging.getLogger("billmind.rag")
 

class Knowledge(RagBaseService):
    """知识库 RAG 门面：索引 agent/knowledge 并在 Milvus 中做相似度检索。

    流程概览::

        Markdown 分块 → Ollama Embedding → Milvus 写入
        用户问题 → 同一 Embedding 模型 → Milvus Top-K → KnowledgeHit

    典型用法::

        rag = RAG()
        rag.index(force=True)     # CLI 全量重建
        hits = rag.search("应急资金要留多少")
    """

    # 常量
    COLLECTION_NAME = "billmind_knowledge"
    
    # 知识库目录
    KNOWLEDGE_DIRS = ("finance",)
    
    # 知识库根目录
    KNOWLEDGE_ROOT = Path(__file__).resolve().parents[1] / "knowledge"
    
    # 有效知识库分类
    VALID_KB = frozenset(KNOWLEDGE_DIRS)

    # 分块大小
    CHUNK_SIZE = 500
    
    # 分块重叠大小
    CHUNK_OVERLAP = 50

    def __init__(self) -> None:
        self._vector_store: Milvus | None = None

    # ------------------------------------------------------------------
    # 对外 API：索引、检索、启动初始化
    # ------------------------------------------------------------------

    def index(
        self,
        *,
        force: bool = False,
        root: Path | None = None,
        dirs: Sequence[str] | None = None,
    ) -> int:
        """
        将知识库 Markdown 写入 Milvus;返回 chunk 数。force=True 时全量重建。
        Args:
            force: 是否全量重建。
            root: 知识库根目录，默认 KNOWLEDGE_ROOT。
            dirs: 子目录名列表，默认 KNOWLEDGE_DIRS。
        Returns:
            int: 索引的 chunk 数。
        """
        base = root or self.KNOWLEDGE_ROOT
        
        # 1.加载知识库文档
        knowledge_docs = self.load_docs(base, dirs)
        
        # 2.将知识库文档切分为 chunk
        chunks = self.docs_to_chunks(knowledge_docs, root=base)
        if not chunks:
            logger.warning("无可用知识正文（占位文档尚未填写），跳过索引")
            return 0


        # 3.chunks 添加到 Milvus
        if force:
            self.add_documents(self.COLLECTION_NAME, chunks, drop_old=True)
        else:
            if self.collection_entity_count(self.COLLECTION_NAME) > 0:
                logger.info("Milvus 集合已有数据，跳过自动索引（可用 --force 重建）")
                return 0
            self.add_documents(self.COLLECTION_NAME, chunks)

        logger.info("已索引 %d 个 chunk（来自 %d 篇文档）", len(chunks), len(knowledge_docs))
        return len(chunks)

    def search(
        self,
        query: str,
        *,
        kb: str | None = None,
        top_k: int | None = None,
    ) -> list[KnowledgeHit]:
        """
        相似度检索;kb 可选，用于限定知识库目录（如 finance)。
        Args:
            query: 用户问题或检索关键词。
            kb: 可选知识库范围:finance(理财);留空则搜索全部。
            top_k: 可选检索结果数量:默认取 env.RAG_TOP_K。
        Returns:
            list[KnowledgeHit]: 检索结果列表。
        """
        if kb and kb not in self.VALID_KB:
            raise ValueError(f"kb 必须是 {sorted(self.VALID_KB)} 之一，收到: {kb!r}")

        k = top_k or get_rag_top_k()
        
        docs = get_vector_store(self.COLLECTION_NAME).similarity_search(
            query.strip(), k=k, expr=f'kb == "{kb}"' if kb else None)
        hits: list[KnowledgeHit] = []
        for doc in docs:
            meta = doc.metadata or {}
            hits.append(
                KnowledgeHit(
                    text=doc.page_content,
                    kb=str(meta.get("kb", "")),
                    source=str(meta.get("source", "")),
                    title=str(meta.get("title", "")),
                )
            )
        return hits