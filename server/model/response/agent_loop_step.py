from __future__ import annotations

from pydantic import ConfigDict
from sqlmodel import SQLModel

from server.model.agent_loop_step import AgentLoopStep


class AgentLoopStepGetListResponse(SQLModel):
    """GET 列表响应（预留 M13 Eval 等内部读取）。"""

    model_config = ConfigDict(from_attributes=True)

    List: list[AgentLoopStep]
