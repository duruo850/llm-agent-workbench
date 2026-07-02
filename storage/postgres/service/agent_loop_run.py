"""AgentLoopRun 业务服务 — 薄 CRUD，入参/出参均为 ``AgentLoopRun`` 模型。"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from server.model.agent_loop_run import AgentLoopRun
from server.model.request.agent_loop_run import AgentLoopRunListQueryRequest
from storage.postgres.service.enter import agent_loop_run_crud


@dataclass
class AgentLoopRunList:
    data: list[AgentLoopRun]
    total_count: int


class AgentLoopRunService:
    async def create(self, db: AsyncSession, row: AgentLoopRun) -> AgentLoopRun:
        created = await agent_loop_run_crud.create(
            db,
            object=row,
            schema_to_select=AgentLoopRun,
            return_as_model=True,
        )
        if created is None:
            raise RuntimeError("create agent_loop_run returned None")
        return created

    async def get_list(
        self,
        db: AsyncSession,
        req: AgentLoopRunListQueryRequest,
    ) -> AgentLoopRunList:
        filters: dict[str, object] = {}
        if req.Id is not None:
            filters["id"] = req.Id
        if req.AccountId is not None:
            filters["account_id"] = req.AccountId
        if req.ConversationId is not None:
            filters["conversation_id"] = req.ConversationId
        if req.ThreadId:
            filters["thread_id"] = req.ThreadId
        if req.TurnId:
            filters["turn_id"] = req.TurnId
        result = await agent_loop_run_crud.get_multi(
            db,
            **filters,
            offset=req.Page * req.PageSize,
            limit=req.PageSize,
            schema_to_select=AgentLoopRun,
            return_as_model=True,
        )
        return AgentLoopRunList(data=result["data"], total_count=result["total_count"])

    async def update(self, db: AsyncSession, row: AgentLoopRun) -> AgentLoopRun | None:
        return await agent_loop_run_crud.update(
            db,
            object={"user_chat_message_id": row.user_chat_message_id},
            id=row.id,
            schema_to_select=AgentLoopRun,
            return_as_model=True,
            one_or_none=True,
        )

    async def delete(self, db: AsyncSession, row: AgentLoopRun) -> None:
        await agent_loop_run_crud.delete(db, id=row.id)


agent_loop_run_service = AgentLoopRunService()
