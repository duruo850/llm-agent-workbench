"""Agent HTTP API — 注入 db session 后转发给 ``agent.runner``。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from agent.runner import invoke_agent
from server.db.session import get_db
from server.model.request.agent import AgentChatRequest
from server.model.response.agent import AgentChatResponse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(
    body: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
) -> AgentChatResponse:
    reply = await invoke_agent(body.message, db=db)
    return AgentChatResponse(reply=reply)
