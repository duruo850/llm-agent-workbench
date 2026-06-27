from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from server.model.base import RequestBase


class AgentChatRequest(RequestBase):
    """POST /agent/chat — 用户自然语言消息，可选图片或 CSV 文件。"""

    message: str = Field(default="", max_length=2000)
    image_data_url: str | None = Field(default=None, max_length=10_000_000)
    file_name: str | None = Field(default=None, max_length=255)
    file_text: str | None = Field(default=None, max_length=2_000_000)
    thread_id: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def message_or_attachment_required(self) -> Self:
        has_image = bool(self.image_data_url)
        has_file = self.file_name is not None and self.file_text is not None
        if not self.message.strip() and not has_image and not has_file:
            raise ValueError("message、image_data_url、file 至少一项非空")
        if has_image and has_file:
            raise ValueError("image_data_url 与 file 不能同时上传")
        if self.file_name is not None and self.file_text is None:
            raise ValueError("file_name 与 file_text 须同时提供")
        if self.file_text is not None and not self.file_name:
            raise ValueError("file_name 与 file_text 须同时提供")
        return self
