from langchain_milvus import Milvus
from langchain_ollama import OllamaEmbeddings
from common.milvus import get_client, get_ollama_embedding_model, get_ollama_uri, get_milvus_uri
from common.milvus import embedding_ready
from common.milvus import available as milvus_available
from langchain_core.documents import Document
from pathlib import Path
from collections.abc import Sequence
from dataclasses import dataclass
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
from typing import List

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


class RagBaseService:

    def __init__(self) -> None:
        # 缓存向量库实例，避免重复创建
        self._vector_stores: dict[str, Milvus] = {} 

    @classmethod
    def available(cls) -> bool:
        """Milvus 是否可达（委托 ``common.milvus.available``）。"""
        return milvus_available()
    
    @classmethod
    def is_ready(cls) -> bool:
        """Milvus 可达且 Ollama embedding 模型可用。"""
        return embedding_ready()
        
    def get_vector_store(self, collection_name: str, *, drop_old: bool = False) -> Milvus:
        """
        获取 LangChain Milvus 向量库（按 collection 缓存，避免重复创建）。

        Args:
            collection_name (str): 集合名称。
            drop_old (bool, optional): 是否删除旧的集合。Defaults to False.

        Returns:
            Milvus: 向量库实例。
        """
        if drop_old:
            self.delete_vector_store(collection_name)
            client = get_client()
            if client.has_collection(collection_name):
                client.drop_collection(collection_name)
        elif collection_name in self._vector_stores:
            return self._vector_stores[collection_name]

        embeddings = OllamaEmbeddings(
            model=get_ollama_embedding_model(),
            base_url=get_ollama_uri(),
        )
        store = Milvus(
            embedding_function=embeddings,
            collection_name=collection_name,
            connection_args={"uri": get_milvus_uri()},
            auto_id=False,
            drop_old=False,
        )
        self._vector_stores[collection_name] = store
        return store

    def delete_vector_store(self, collection_name: str) -> None:
        """删除缓存的向量库实例。

        Args:
            collection_name (str): 集合名称。
        """
        self._vector_stores.pop(collection_name, None)

    def add_documents(
        self,
        collection_name: str,
        documents: list[Document],
        *,
        drop_old: bool = False,
    ) -> List[str]:
        """
        将 documents 添加到向量库。

        Args:
            collection_name: 集合名称。
            documents: 要添加的 documents 列表。
            drop_old: 是否删除旧的 documents。
        Return:
            List[str]: 添加的 documents 的 列表。
        """
        return self.get_vector_store(collection_name, drop_old=drop_old).add_documents(documents)
        
        
    @classmethod
    def collection_entity_count(cls, collection_name: str) -> int:
        """
        获取集合内实体数;集合不存在时返回 0。
        Args:
            collection_name: 集合名称。
        Returns:
            int: 集合内实体数。
        """
        try:
            client = get_client()
            if not client.has_collection(collection_name):
                return 0
            stats = client.get_collection_stats(collection_name)
            return int(stats.get("row_count", 0))
        except Exception:
            return 0
        
    @classmethod
    def delete_by_expr(cls, collection_name: str, expr: str) -> None:
        """
        根据表达式删除集合内的实体。
        Args:
            collection_name: 集合名称。
            expr: 表达式。
        """
        client = get_client()
        if not client.has_collection(collection_name):
            return
        client.delete(collection_name=collection_name, filter=expr)
        

    # ------------------------------------------------------------------
    # 知识库 Markdown 解析与分块
    # ------------------------------------------------------------------

    @staticmethod
    def parse_markdown(path: Path, default_kb: str) -> KnowledgeDoc:
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
        kb_dirs: Sequence[str] | None = None,
    ) -> list[KnowledgeDoc]:
        """
        扫描 dirs 下所有 .md（跳过 README）。
        Args:
            root: 知识库根目录，默认 KNOWLEDGE_ROOT。
            kb_dirs: 子目录名列表，默认 KNOWLEDGE_DIRS。
        Returns:
            list[KnowledgeDoc]: 知识库文档列表。
        """
        docs: list[KnowledgeDoc] = []
        for kb_dir in kb_dirs:
            folder = root / kb_dir
            if not folder.is_dir():
                continue
            docs.extend(
                self.parse_markdown(path, kb_dir)
                for path in sorted(folder.glob("*.md"))
                if path.name.lower() != "readme.md"
            )
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
