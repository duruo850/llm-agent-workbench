"""BillMind 知识库 RAG — 扫描 Markdown、Ollama 向量化、Milvus 存储与检索。"""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from langchain_core.documents import Document
from langchain_milvus import Milvus
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymilvus import MilvusClient, connections

from common.env import (
    get_milvus_uri,
    get_ollama_uri,
    get_ollama_embedding_model,
    get_rag_top_k,
)

logger = logging.getLogger("billmind.rag")


def _patch_milvus_client_orm_sync() -> None:
    """LangChain Milvus 混用 MilvusClient + ORM Collection，需为 client alias 注册 ORM 连接。"""
    if getattr(MilvusClient.__init__, "_billmind_patched", False):
        return

    _orig_init = MilvusClient.__init__

    def _wrapped(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        alias = getattr(self, "_using", None)
        if not alias or connections.has_connection(alias):
            return
        uri = kwargs.get("uri")
        if uri is None and args:
            uri = args[0]
        if not uri:
            uri = get_milvus_uri()
        connections.connect(alias=alias, uri=uri)

    _wrapped._billmind_patched = True  # type: ignore[attr-defined]
    MilvusClient.__init__ = _wrapped  # type: ignore[method-assign]


_patch_milvus_client_orm_sync()

# Markdown frontmatter：---\ntitle: ...\nkb: ...\n---\n正文
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)


@dataclass(frozen=True)
class KnowledgeDoc:
    """一篇知识库 Markdown 解析结果。"""

    path: Path
    kb: str
    title: str
    body: str


@dataclass(frozen=True)
class KnowledgeHit:
    """检索命中的一条 chunk。"""

    text: str   # 检索命中的一段文本
    kb: str     # 知识库分类
    source: str # 来源文件
    title: str  # 标题
    score: float | None = None # 相似度得分
 

class RAG:
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
    # Milvus 连接与向量库
    # ------------------------------------------------------------------

    def available(self) -> bool:
        """Milvus 是否可达（仅 ping，不保证已有索引数据）。"""
        try:
            MilvusClient(uri=get_milvus_uri())
            return True
        except Exception as exc:
            logger.warning("Milvus 不可达 (%s): %s", get_milvus_uri(), exc)
            return False

    def is_ready(self) -> bool:
        """RAG 是否可用（当前等同 Milvus 可达）。"""
        return self.available()

    def _get_vector_store(self, *, drop_old: bool = False) -> Milvus:
        """
        获取 LangChain Milvus 向量库;drop_old=True 时删除旧集合并重建。
        Args:
            drop_old: 是否删除旧的 documents。
        Returns:
            Milvus: 向量库实例。
        """
        if drop_old:
            self._vector_store = None
            client = MilvusClient(uri=get_milvus_uri())
            if client.has_collection(self.COLLECTION_NAME):
                client.drop_collection(self.COLLECTION_NAME)

        if self._vector_store is not None:
            return self._vector_store

        embeddings = OllamaEmbeddings(
            model=get_ollama_embedding_model(),
            base_url=get_ollama_uri(),
        )
        self._vector_store = Milvus(
            embedding_function=embeddings,
            collection_name=self.COLLECTION_NAME,
            connection_args={"uri": get_milvus_uri()},
            auto_id=True,
            drop_old=False,
        )
        return self._vector_store

    def _collection_entity_count(self) -> int:
        """
        集合内实体数;集合不存在时返回 0。
        Returns:
            int: 集合内实体数。
        """
        try:
            client = MilvusClient(uri=get_milvus_uri())
            if not client.has_collection(self.COLLECTION_NAME):
                return 0
            stats = client.get_collection_stats(self.COLLECTION_NAME)
            return int(stats.get("row_count", 0))
        except Exception:
            return 0

    def _add_documents(self, documents: list[Document], *, drop_old: bool = False) -> None:
        """
        将 documents 添加到向量库。

        Args:
            documents: 要添加的 documents 列表。
            drop_old: 是否删除旧的 documents。
        """
        self._get_vector_store(drop_old=drop_old).add_documents(documents)

    def _similarity_search(
        self,
        query: str,
        *,
        k: int,
        kb: str | None = None,
    ) -> list[Document]:
        """
        相似度检索;kb 可选，用于限定知识库目录（如 finance)。

        Args:
            query: 用户问题或检索关键词。
            k: 检索结果数量。
            kb: 可选知识库范围:finance(理财);留空则搜索全部。

        Returns:
            list[Document]: _description_
        """
        expr = f'kb == "{kb}"' if kb else None
        store = self._get_vector_store()
        return store.similarity_search(query, k=k, expr=expr)

    # ------------------------------------------------------------------
    # 知识库 Markdown 解析与分块
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_markdown(path: Path, default_kb: str) -> KnowledgeDoc:
        """
        解析 Markdown 文件;获取标题、知识库分类、正文。
        Args:
            path: 文件路径。
            default_kb: 默认知识库分类。
        Returns:
            KnowledgeDoc: 解析后的知识库文档。
        """
        raw = path.read_text(encoding="utf-8")
        title = path.stem
        kb = default_kb
        body = raw.strip()

        if match := _FRONTMATTER_RE.match(raw):
            meta_block, body = match.group(1), match.group(2).strip()
            for line in meta_block.splitlines():
                if line.startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                elif line.startswith("kb:"):
                    kb = line.split(":", 1)[1].strip()

        return KnowledgeDoc(path=path, kb=kb, title=title, body=body)

    def load_docs(
        self,
        root: Path | None = None,
        dirs: Sequence[str] | None = None,
    ) -> list[KnowledgeDoc]:
        """
        扫描 dirs 下所有 .md（跳过 README）。
        Args:
            root: 知识库根目录，默认 KNOWLEDGE_ROOT。
            dirs: 子目录名列表，默认 KNOWLEDGE_DIRS。
        Returns:
            list[KnowledgeDoc]: 知识库文档列表。
        """
        base = root or self.KNOWLEDGE_ROOT
        kb_dirs = dirs if dirs is not None else self.KNOWLEDGE_DIRS
        docs: list[KnowledgeDoc] = []
        for kb_dir in kb_dirs:
            folder = base / kb_dir
            if not folder.is_dir():
                continue
            [docs.append(self._parse_markdown(path, kb_dir))
             for path in sorted(folder.glob("*.md"))
             if path.name.lower() != "readme.md"]
        return docs

    def docs_to_chunks(
        self,
        knowledge_docs: list[KnowledgeDoc],
        *,
        root: Path | None = None,
    ) -> list[Document]:
        """
        长文切分为 chunk,跳过占位正文"（正文待填写）"。
        Args:
            knowledge_docs: 知识库文档列表。
            root: 用于 metadata.source 相对路径，默认 KNOWLEDGE_ROOT。
        Returns:
            list[Document]: 切分后的 chunk 列表。
        """
        source_base = (root or self.KNOWLEDGE_ROOT).parent
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.CHUNK_SIZE,
            chunk_overlap=self.CHUNK_OVERLAP,
        )
        chunks: list[Document] = []
        for item in knowledge_docs:
            if not item.body or item.body == "（正文待填写）":
                continue
            text = f"{item.title}\n\n{item.body}"
            chunks.extend(
                Document(
                    page_content=piece,
                    metadata={
                        "kb": item.kb,
                        "source": str(item.path.relative_to(source_base)),
                        "title": item.title,
                    },
                )
                for piece in splitter.split_text(text)
            )
        return chunks

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
            self._add_documents(chunks, drop_old=True)
        else:
            if self._collection_entity_count() > 0:
                logger.info("Milvus 集合已有数据，跳过自动索引（可用 --force 重建）")
                return 0
            self._add_documents(chunks)

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
        docs = self._similarity_search(query.strip(), k=k, kb=kb or None)
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