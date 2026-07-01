"""ChatMessage HTTP API - 编排与 Request/Response 转换."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.session import get_db
from server.model.account import Account
from server.model.request.chat_message import ChatMessageListQueryRequest
from server.model.request.conversation import ConversationListQueryRequest
from server.model.response.chat_message import ChatMessageGetListResponse
from storage.postgres.service.account import get_current_account
from storage.postgres.service.chat_message import chat_message_service
from storage.postgres.service.conversation import conversation_service

router = APIRouter(prefix="/conversations", tags=["chat-messages"])


@router.get("/{thread_id}/messages", response_model=ChatMessageGetListResponse)
async def list_conversation_messages(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    account: Account = Depends(get_current_account),
) -> ChatMessageGetListResponse:
    conv_result = await conversation_service.get_list(
        db,
        ConversationListQueryRequest(
            AccountId=account.id,
            ThreadId=thread_id,
            Page=0,
            PageSize=1,
        ),
    )
    conversation = conv_result.data[0] if conv_result.data else None
    if conversation is None or conversation.id is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    msg_result = await chat_message_service.get_list(
        db,
        ChatMessageListQueryRequest(
            ConversationId=conversation.id,
            Page=0,
            PageSize=1000,
        ),
    )
    rows = sorted(msg_result.data, key=lambda row: row.id or 0)
    return ChatMessageGetListResponse(List=rows)
