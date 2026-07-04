"""AgentLoopStep 业务服务 — 薄 CRUD，入参/出参均为 ``AgentLoopStep`` 模型。"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from server.model.agent_loop_step import AgentLoopStep
from server.model.request.agent_loop_step import AgentLoopStepListQueryRequest
from storage.postgres.service.enter import agent_loop_step_crud


@dataclass
class AgentLoopStepList:
    data: list[AgentLoopStep]
    total_count: int


class AgentLoopStepService:
    async def create(
        self,
        db: AsyncSession,
        row: AgentLoopStep,
        *,
        commit: bool = True,
    ) -> AgentLoopStep:
        created = await agent_loop_step_crud.create(
            db,
            object=row,
            schema_to_select=AgentLoopStep,
            return_as_model=True,
            commit=commit,
        )
        if created is None:
            raise RuntimeError("create agent_loop_step returned None")
        return created

    async def get_list(
        self,
        db: AsyncSession,
        req: AgentLoopStepListQueryRequest,
    ) -> AgentLoopStepList:
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
        result = await agent_loop_step_crud.get_multi(
            db,
            **filters,
            offset=req.Page * req.PageSize,
            limit=req.PageSize,
            schema_to_select=AgentLoopStep,
            return_as_model=True,
        )
        return AgentLoopStepList(data=result["data"], total_count=result["total_count"])

    async def update(self, db: AsyncSession, row: AgentLoopStep) -> AgentLoopStep | None:
        return await agent_loop_step_crud.update(
            db,
            object={
                "user_chat_message_id": row.user_chat_message_id,
                "token_usage": row.token_usage,
                "node_name": row.node_name,
                "tool_name": row.tool_name,
            },
            id=row.id,
            schema_to_select=AgentLoopStep,
            return_as_model=True,
            one_or_none=True,
        )

    async def delete(self, db: AsyncSession, row: AgentLoopStep) -> None:
        await agent_loop_step_crud.delete(db, id=row.id)


agent_loop_step_service = AgentLoopStepService()
