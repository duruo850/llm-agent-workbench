"""Agent HTTP API — 注入 db session 后转发给 ``agent.runner``。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from agent.runner import invoke_agent
from agent.vision import parse_receipt_image
from server.db.session import get_db
from server.model.request.agent import AgentChatRequest
from server.model.response.agent import AgentChatResponse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    body: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentChatResponse:
    if body.image_data_url:
        try:
            vision_text = await parse_receipt_image(body.image_data_url)
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        message = (
            f"{body.message.strip()}\n\n{vision_text}"
            if body.message.strip()
            else vision_text
        )
    else:
        message = body.message

    reply = await invoke_agent(message, db=db)
    return AgentChatResponse(reply=reply)
