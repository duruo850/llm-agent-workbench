"""Agent HTTP API — 注入 db session 后转发给 ``Agent``。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from agent import Agent
from server.db.session import get_db
from server.service.account import get_current_account
from server.model.account import Account
from server.model.request.agent import AgentChatRequest
from server.model.response.agent import AgentChatResponse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    body: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> AgentChatResponse:
    if body.image_data_url:
        try:
            vision_text = await Agent.parse_image(body.image_data_url)
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        message = (
            f"{body.message.strip()}\n\n{vision_text}"
            if body.message.strip()
            else vision_text
        )
    else:
        message = body.message

    reply, thread_id = await Agent.invoke(
        message, db=db,account_id=account.id, thread_id=body.thread_id
    )
    return AgentChatResponse(reply=reply, thread_id=thread_id)
