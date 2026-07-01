"""Conversation HTTP API - Request/Response 与 ``Conversation`` 模型转换."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from server.model.account import Account
from server.model.request.conversation import ConversationListQueryRequest
from server.model.response.conversation import ConversationGetListResponse
from storage.postgres.service.account import get_current_account
from storage.postgres.service.conversation import conversation_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=ConversationGetListResponse)
async def list_conversations(
    query: Annotated[ConversationListQueryRequest, Depends()],
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> ConversationGetListResponse:
    req = query.model_copy(update={"AccountId": account.id})
    result = await conversation_service.get_list(db, req)
    return ConversationGetListResponse(List=result.data)
