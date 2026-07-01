from __future__ import annotations

from datetime import datetime

from server.model.base import RequestBase
from server.model.conversation import Conversation


class ConversationCreateRequest(RequestBase):
    """POST /conversations - 创建会话."""

    Data: Conversation


class ConversationUpdateRequest(RequestBase):
    """PATCH /conversations/{id} - 部分更新."""

    Data: Conversation


class ConversationListQueryRequest(RequestBase):
    """GET /conversations - 列表查询参数."""

    Page: int = 0
    PageSize: int = 100
    Keyword: str | None = None
    Id: int | None = None
    AccountId: int | None = None
    ThreadId: str = ""
    Title: str | None = None
    CreatedAt: datetime | None = None
    UpdatedAt: datetime | None = None
