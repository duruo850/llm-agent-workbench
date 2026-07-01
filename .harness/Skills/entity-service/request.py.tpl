"""{Entity} HTTP 请求模板 (档位 E).

复制为 server/model/request/{entity}.py, 替换 {Entity} / {entity}.
说明见同目录 SKILL.md § 档位 E.
标杆: server/model/request/chat_message.py

约定:
  - Create/Update 用 ``Data: {Entity}`` 传递 ORM 模型 (非逐字段展开)
  - API: ``body.Data`` 补全租户字段后交 service.create/update
  - POST / PATCH 响应 status_code=200, 无 body
  - ListQueryRequest 含分页默认值 + 可选过滤字段 (PascalCase)
"""

from __future__ import annotations

from server.model.base import RequestBase
from server.model.{entity} import {Entity}


class {Entity}CreateRequest(RequestBase):
    """POST /{entities} - 创建."""

    Data: {Entity}


class {Entity}UpdateRequest(RequestBase):
    """PATCH /{entities}/{{id}} - 部分更新."""

    Data: {Entity}


class {Entity}ListQueryRequest(RequestBase):
    """GET /{entities} - 列表查询参数."""


    Keyword: str | None = None
    # TODO: 按实体加可选过滤字段, 如 AccountId: int | None = None
