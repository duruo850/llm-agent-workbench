"""M12 意图分类调试 API — GET /intent/classify。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from agent.intent import intent_manager
from common.env import is_intent_enabled
from server.model.response.intent import IntentClassifyResponse

router = APIRouter(prefix="/intent", tags=["intent"])


@router.get("/classify", response_model=IntentClassifyResponse)
async def classify_intent(
    q: str = Query(min_length=1, description="用户消息"),
    method: str | None = Query(default=None, description="rule | embedding | bert | hybrid"),
) -> IntentClassifyResponse:
    """
    意图分类调试 API — GET /intent/classify。
    """
    if not is_intent_enabled():
        raise HTTPException(
            status_code=503,
            detail="意图识别未开启",
        )

    allowed = {"rule", "embedding", "bert", "hybrid", None}
    if method is not None and method not in allowed:
        raise HTTPException(status_code=400, detail=f"method 无效: {method}")

    result = intent_manager.classify(q, method=method)  # type: ignore[arg-type]
    return IntentClassifyResponse(
        query=q,
        scene=result.scene,
        confidence=result.confidence,
        method=str(result.method),
        candidates=[
            {"scene": c.scene, "confidence": c.confidence}
            for c in result.candidates
        ],
    )
