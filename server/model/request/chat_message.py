from __future__ import annotations

from datetime import datetime

from server.model.base import RequestBase
from server.model.chat_message import ChatMessage


class ChatMessageCreateRequest(RequestBase):
    """POST /chat-messages - 创建单条消息."""

    Data: ChatMessage


class ChatMessageUpdateRequest(RequestBase):
    """PATCH /chat-messages/{id} - 部分更新."""

    Data: ChatMessage


class ChatMessageListQueryRequest(RequestBase):
    """GET /chat-messages - 列表查询参数."""

    Page: int = 0
    PageSize: int = 100
    Keyword: str | None = None
    Id: int | None = None
    ConversationId: int | None = None
    Role: str = ""
    CreatedAt: datetime | None = None
