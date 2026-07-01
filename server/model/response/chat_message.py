from __future__ import annotations

from pydantic import ConfigDict
from sqlmodel import SQLModel

from server.model.chat_message import ChatMessage


class ChatMessageGetListResponse(SQLModel):
    """GET /conversations/{thread_id}/messages 响应."""

    model_config = ConfigDict(from_attributes=True)

    List: list[ChatMessage]
