"""知识库 RAG API 响应模型。"""

from __future__ import annotations

from pydantic import BaseModel


class KnowledgeHitResponse(BaseModel):
    text: str  # 检索命中的一段文本
    kb: str     # 知识库分类
    source: str # 来源文件
    title: str  # 标题
    score: float | None = None # 相似度得分


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeHitResponse]
