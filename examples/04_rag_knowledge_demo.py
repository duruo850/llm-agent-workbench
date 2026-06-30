#!/usr/bin/env python3
"""M7 RAG demo — 索引 agent/knowledge 并检索。

用法::

    docker compose up -d milvus
    ollama pull nomic-embed-text
    .venv/bin/python3.14 examples/04_rag_knowledge_demo.py
    .venv/bin/python3.14 examples/04_rag_knowledge_demo.py --query "应急资金"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from agent.rag import milvus_available, rag


def main() -> None:
    parser = argparse.ArgumentParser(description="BillMind RAG 知识库 demo")
    parser.add_argument("--query", default="你会啥理财知识", help="检索问题")
    parser.add_argument("--kb", default="", help="finance")
    parser.add_argument("--force", action="store_true", help="强制重建索引")
    args = parser.parse_args()

    if not milvus_available():
        print("Milvus 不可达，请先: docker compose up -d milvus")
        sys.exit(1)

    count = rag.index(force=args.force)
    print(f"indexed chunks: {count}")

    kb = args.kb.strip() or None
    hits = rag.search(args.query, kb=kb)
    if not hits:
        print("无命中（请确认 agent/knowledge 已填写正文并 --force 重建索引）")
        sys.exit(0)

    for i, hit in enumerate(hits, 1):
        print(f"\n--- hit {i} [{hit.kb}] {hit.title} ---")
        print(hit.text[:300])
        print(f"source: {hit.source}")


if __name__ == "__main__":
    main()
