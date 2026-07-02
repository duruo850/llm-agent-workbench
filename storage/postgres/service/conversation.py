"""Conversation 业务服务 - 薄 CRUD, 入参/出参均为 ``Conversation`` 模型."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from server.model.conversation import Conversation
from server.model.request.conversation import ConversationListQueryRequest
from storage.postgres.service.enter import conversation_crud
from storage.postgres.service.chat_message import chat_message_service
from server.model.chat_message import ChatMessage
from server.model.request.chat_message import ChatMessageListQueryRequest


@dataclass
class ConversationList:
    data: list[Conversation]
    total_count: int


class ConversationService:
    async def create(self, db: AsyncSession, conversation: Conversation) -> Conversation:
        created = await conversation_crud.create(
            db,
            object=conversation,
            schema_to_select=Conversation,
            return_as_model=True,
        )
        if created is None:
            raise RuntimeError("create conversation returned None")
        return created
    
    async def ensure(
        self,
        db: AsyncSession,
        account_id: int,
        thread_id: str,
        title: str | None,
    ) -> Conversation:
        """确保会话存在，如果不存在则创建会话
        Args:
            db (AsyncSession): 数据库会话
            account_id (int): 账户 ID
            thread_id (str): 会话 ID
            title (str): 会话标题

        Returns:
            Conversation: 会话
        """
        # 获取会话
        conversation_result = await self.get_list(
            db,
            ConversationListQueryRequest(
                AccountId=account_id,
                ThreadId=thread_id,
                Page=0,
                PageSize=1,
            ),
        )
        if conversation_result.data:
            return conversation_result.data[0]
        return await self.create(
            db,
            Conversation(account_id=account_id, thread_id=thread_id, title=title),
        )

    async def get_list(
        self,
        db: AsyncSession,
        req: ConversationListQueryRequest,
    ) -> ConversationList:
        filters: dict[str, object] = {}
        if req.Id is not None:
            filters["id"] = req.Id
        if req.ThreadId:
            filters["thread_id"] = req.ThreadId
        if req.AccountId is not None:
            filters["account_id"] = req.AccountId
        result = await conversation_crud.get_multi(
            db,
            **filters,
            offset=req.Page * req.PageSize,
            limit=req.PageSize,
            schema_to_select=Conversation,
            return_as_model=True,
        )
        return ConversationList(data=result["data"], total_count=result["total_count"])

    async def update(self, db: AsyncSession, conversation: Conversation) -> Conversation | None:
        return await conversation_crud.update(
            db,
            object={"title": conversation.title},
            id=conversation.id,
            account_id=conversation.account_id,
            schema_to_select=Conversation,
            return_as_model=True,
            one_or_none=True,
        )

    async def delete(self, db: AsyncSession, conversation: Conversation) -> None:
        await conversation_crud.delete(
            db, id=conversation.id, account_id=conversation.account_id
        )

    async def get_chat_messages(
        self,
        db: AsyncSession,
        query: ConversationListQueryRequest,
    ) -> list[ChatMessage] | None:
        """按 thread 读取会话下全部消息 (按 ``id`` 升序)."""
        conv_result = await self.get_list(db, query)
        conversation = conv_result.data[0] if conv_result.data else None
        if conversation is None or conversation.id is None:
            return None

        msg_result = await chat_message_service.get_list(db, ChatMessageListQueryRequest(ConversationId=conversation.id, Page=0, PageSize=1000))
        return sorted(msg_result.data, key=lambda row: row.id or 0)

conversation_service = ConversationService()
