from __future__ import annotations

from pydantic import Field

from server.model.base import ResponseBase


class AgentChatResponse(ResponseBase):
    """POST /agent/chat — Agent 自然语言回复。"""

    reply: str = Field(min_length=1)
    thread_id: str = Field(min_length=1)
