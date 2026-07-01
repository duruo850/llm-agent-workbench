"""ChatMessage 业务服务 - 薄 CRUD, 入参/出参均为 ``ChatMessage`` 模型."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from server.model.chat_message import ChatMessage
from server.model.request.chat_message import ChatMessageListQueryRequest
from storage.postgres.service.enter import chat_message_crud


@dataclass
class ChatMessageList:
    data: list[ChatMessage]
    total_count: int


class ChatMessageService:
    async def create(self, db: AsyncSession, message: ChatMessage) -> ChatMessage:
        created = await chat_message_crud.create(
            db,
            object=message,
            schema_to_select=ChatMessage,
            return_as_model=True,
        )
        if created is None:
            raise RuntimeError("create chat_message returned None")
        return created

    async def get_list(
        self,
        db: AsyncSession,
        req: ChatMessageListQueryRequest,
    ) -> ChatMessageList:
        filters: dict[str, object] = {}
        if req.Id is not None:
            filters["id"] = req.Id
        if req.ConversationId is not None:
            filters["conversation_id"] = req.ConversationId
        if req.Role:
            filters["role"] = req.Role
        result = await chat_message_crud.get_multi(
            db,
            **filters,
            offset=req.Page * req.PageSize,
            limit=req.PageSize,
            schema_to_select=ChatMessage,
            return_as_model=True,
        )
        return ChatMessageList(data=result["data"], total_count=result["total_count"])

    async def update(self, db: AsyncSession, message: ChatMessage) -> ChatMessage | None:
        return await chat_message_crud.update(
            db,
            object={"content": message.content, "role": message.role},
            id=message.id,
            schema_to_select=ChatMessage,
            return_as_model=True,
            one_or_none=True,
        )

    async def delete(self, db: AsyncSession, message: ChatMessage) -> None:
        await chat_message_crud.delete(db, id=message.id)


chat_message_service = ChatMessageService()
