"""方案 2 — EmbeddingClassifier: Ollama 向量余弦相似度分类。"""

from __future__ import annotations

import logging
import math
from typing import Sequence

from langchain_ollama import OllamaEmbeddings

from agent.common.skill_registry import skill_registry
from agent.intent.manager import IntentCandidate, IntentResult
from common.env import get_intent_embedding_threshold, get_ollama_embedding_model, get_ollama_uri

logger = logging.getLogger("billmind.intent.embedding")


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class EmbeddingClassifier:
    """启动时预计算各 category description 向量，查询时余弦 Top-1。"""

    def __init__(self) -> None:
        self._embeddings: OllamaEmbeddings | None = None
        self._category_vectors: dict[str, list[float]] = {}
        self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    def prepare(self) -> bool:
        """预向量化 category description；Ollama 不可用时返回 False。"""
        if self._ready:
            return True
        try:
            self._embeddings = OllamaEmbeddings(
                model=get_ollama_embedding_model(),
                base_url=get_ollama_uri(),
            )
            self._category_vectors.clear()
            for category_id in skill_registry.all_categories():
                defn = skill_registry.get_category_def(category_id)
                self._category_vectors[category_id] = self._embeddings.embed_query(
                    defn.description
                )
            self._ready = True
            logger.info(
                "EmbeddingClassifier warmed up (%s categories)",
                len(self._category_vectors),
            )
            return True
        except Exception as exc:
            logger.warning("EmbeddingClassifier warmup failed: %s", exc)
            self._embeddings = None
            self._category_vectors.clear()
            self._ready = False
            return False

    def warmup(self) -> bool:
        """向后兼容别名。"""
        return self.prepare()

    def classify(self, text: str, *, top_k: int = 3) -> IntentResult | None:
        if not self._ready and not self.prepare():
            return None

        normalized = text.strip()
        if not normalized or self._embeddings is None:
            return None

        try:
            query_vec = self._embeddings.embed_query(normalized)
        except Exception as exc:
            logger.warning("embed_query failed: %s", exc)
            return None

        scored: list[tuple[str, float]] = []
        for category_id, category_vec in self._category_vectors.items():
            scored.append((category_id, _cosine_similarity(query_vec, category_vec)))
        scored.sort(key=lambda item: item[1], reverse=True)

        threshold = get_intent_embedding_threshold()
        top = scored[:top_k]
        candidates = tuple(IntentCandidate(scene=s, confidence=c) for s, c in top)
        if not top or top[0][1] < threshold:
            return None

        best_scene, best_score = top[0]
        return IntentResult(
            scene=best_scene,
            confidence=best_score,
            method="embedding",
            candidates=candidates,
        )
