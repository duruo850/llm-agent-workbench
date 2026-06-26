from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from server.model.base import RequestBase


class AgentChatRequest(RequestBase):
    """POST /agent/chat — 用户自然语言消息，可选支付截图 data URL。"""

    message: str = Field(default="", max_length=2000)
    image_data_url: str | None = Field(default=None, max_length=10_000_000)
    thread_id: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def message_or_image_required(self) -> Self:
        if not self.message.strip() and not self.image_data_url:
            raise ValueError("message 与 image_data_url 至少一项非空")
        return self
