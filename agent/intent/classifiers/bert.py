"""方案 3 — BertClassifier: sklearn Tfidf + LogisticRegression 序列分类。"""

from __future__ import annotations

import logging
from pathlib import Path

from agent.intent.manager import LABEL_TO_CATEGORY, IntentCandidate, IntentResult
from common.env import get_intent_bert_threshold

logger = logging.getLogger("billmind.intent.bert")

_MODEL_DIR = Path(__file__).resolve().parent
_SKLEARN_PIPELINE = None


class BertClassifier:
    """加载本目录 ``sklearn_pipeline.joblib`` 做推理。"""

    def __init__(self, model_path: str | Path | None = None) -> None:
        self._model_path = Path(model_path) if model_path else _MODEL_DIR
        self._ready = False

    @property
    def ready(self) -> bool:
        return self._ready

    def prepare(self) -> bool:
        global _SKLEARN_PIPELINE
        if self._ready:
            return True

        sklearn_path = self._model_path / "sklearn_pipeline.joblib"
        if not sklearn_path.is_file():
            logger.warning("sklearn pipeline not found at %s", sklearn_path)
            return False

        try:
            import joblib

            _SKLEARN_PIPELINE = joblib.load(sklearn_path)
            self._ready = True
            logger.info("BertClassifier loaded sklearn pipeline from %s", sklearn_path)
            return True
        except Exception as exc:
            logger.warning("sklearn pipeline load failed: %s", exc)
            _SKLEARN_PIPELINE = None
            self._ready = False
            return False

    def warmup(self) -> bool:
        """向后兼容别名。"""
        return self.prepare()

    def classify(self, text: str, *, top_k: int = 3) -> IntentResult | None:
        if not self._ready and not self.prepare():
            return None

        normalized = text.strip()
        if not normalized:
            return None

        global _SKLEARN_PIPELINE
        if _SKLEARN_PIPELINE is None:
            return None
        try:
            import numpy as np

            proba = _SKLEARN_PIPELINE.predict_proba([normalized])[0]
            classes = _SKLEARN_PIPELINE.classes_
            top_indices = np.argsort(proba)[::-1][:top_k]
            threshold = get_intent_bert_threshold()
            candidates: list[IntentCandidate] = []
            for idx in top_indices:
                label = int(classes[idx])
                score = float(proba[idx])
                category_id = LABEL_TO_CATEGORY.get(label)
                if category_id:
                    candidates.append(IntentCandidate(scene=category_id, confidence=score))
            if not candidates or candidates[0].confidence < threshold:
                return None
            best = candidates[0]
            return IntentResult(
                scene=best.scene,
                confidence=best.confidence,
                method="bert",
                candidates=tuple(candidates),
            )
        except Exception as exc:
            logger.warning("sklearn classify failed: %s", exc)
            return None
