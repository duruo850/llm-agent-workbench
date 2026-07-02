from __future__ import annotations

from datetime import datetime

from server.model.agent_loop_step import AgentLoopStep
from server.model.base import RequestBase


class AgentLoopStepCreateRequest(RequestBase):
    """内部创建 — 档位 E ``Data`` 包装。"""

    Data: AgentLoopStep


class AgentLoopStepUpdateRequest(RequestBase):
    """内部更新 — 档位 E ``Data`` 包装。"""

    Data: AgentLoopStep


class AgentLoopStepListQueryRequest(RequestBase):
    """列表查询 — 供 Service ``get_list`` 使用。"""

    Page: int = 0
    PageSize: int = 100
    Id: int | None = None
    AccountId: int | None = None
    ConversationId: int | None = None
    ThreadId: str = ""
    TurnId: str = ""
    CreatedAt: datetime | None = None
