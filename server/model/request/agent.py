from __future__ import annotations

from pydantic import Field

from server.model.base import RequestBase


class AgentChatRequest(RequestBase):
    """POST /agent/chat — 用户自然语言消息。"""

    message: str = Field(min_length=1, max_length=2000)
