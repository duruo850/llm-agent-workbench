"""{Entity} 业务服务 - 薄 CRUD 模板 (档位 E).

复制为 storage/postgres/service/{entity}.py, 替换 {Entity} / {entity} / 过滤字段.
说明见同目录 SKILL.md § 档位 E.
标杆: storage/postgres/service/chat_message.py
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from server.model.{entity} import {Entity}
from server.model.request.{entity} import {Entity}ListQueryRequest
from storage.postgres.service.enter import {entity}_crud


@dataclass
class {Entity}List:
    data: list[{Entity}]
    total_count: int


class {Entity}Service:
    async def create(self, db: AsyncSession, row: {Entity}) -> {Entity}:
        created = await {entity}_crud.create(
            db,
            object=row,
            schema_to_select={Entity},
            return_as_model=True,
        )
        if created is None:
            raise RuntimeError("create {entity} returned None")
        return created

    async def get_list(
        self,
        db: AsyncSession,
        req: {Entity}ListQueryRequest,
    ) -> {Entity}List:
        filters: dict[str, object] = {}
        # TODO: 非空字段写入 filters, 如:
        # if req.AccountId is not None:
        #     filters["account_id"] = req.AccountId
        result = await {entity}_crud.get_multi(
            db,
            **filters,
            offset=req.Page * req.PageSize,
            limit=req.PageSize,
            schema_to_select={Entity},
            return_as_model=True,
        )
        return {Entity}List(data=result["data"], total_count=result["total_count"])

    async def update(self, db: AsyncSession, row: {Entity}) -> {Entity} | None:
        return await {entity}_crud.update(
            db,
            object=row.model_dump(exclude_unset=True, exclude={"id"}),
            id=row.id,
            schema_to_select={Entity},
            return_as_model=True,
            one_or_none=True,
        )

    async def delete(self, db: AsyncSession, row: {Entity}) -> None:
        await {entity}_crud.delete(db, id=row.id)


{entity}_service = {Entity}Service()
