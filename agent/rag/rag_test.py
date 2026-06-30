"""知识库扫描与分块单测 — 不依赖 Milvus。"""

from __future__ import annotations

from agent.rag import KnowledgeDoc, rag


def test_load_knowledge_docs_count() -> None:
    docs = rag.load_docs(rag.KNOWLEDGE_ROOT)
    assert len(docs) == 10


def test_docs_to_chunks_skips_empty_placeholder() -> None:
    placeholder = KnowledgeDoc(
        path=rag.KNOWLEDGE_ROOT / "finance" / "01_预算管理.md",
        kb="finance",
        title="占位",
        body="（正文待填写）",
    )
    assert rag.docs_to_chunks([placeholder]) == []


def test_docs_to_chunks_with_body() -> None:
    doc = KnowledgeDoc(
        path=rag.KNOWLEDGE_ROOT / "finance" / "03_应急资金.md",
        kb="finance",
        title="应急资金",
        body="紧急备用金指可覆盖 3–6 个月必要支出的现金储备。",
    )
    chunks = rag.docs_to_chunks([doc])
    assert len(chunks) == 1
    assert chunks[0].metadata["kb"] == "finance"
    assert "紧急备用金" in chunks[0].page_content
