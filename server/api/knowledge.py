"""知识库 RAG API — GET /knowledge/search。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from storage.rag.knowledge import knowledge
from common.milvus import embedding_ready
from server.model.response.knowledge import KnowledgeHitResponse, KnowledgeSearchResponse

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/search", response_model=KnowledgeSearchResponse)
async def knowledge_search(
    q: str = Query(min_length=1, description="检索关键词或问题"),
    kb: str | None = Query(default=None, description="finance"),
) -> KnowledgeSearchResponse:
    if not embedding_ready():
        raise HTTPException(status_code=503, detail="RAG 未就绪（Milvus 不可用）")

    try:
        hits = knowledge.search(q, kb=kb)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return KnowledgeSearchResponse(
        query=q,
        results=[
            KnowledgeHitResponse(
                text=hit.text,
                kb=hit.kb,
                source=hit.source,
                title=hit.title,
                score=hit.score,
            )
            for hit in hits
        ],
    )
