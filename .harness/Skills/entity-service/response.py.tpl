"""{Entity} HTTP 响应模板 (档位 E).

复制为 server/model/response/{entity}.py, 替换 {Entity} / {entity}.
说明见同目录 SKILL.md § 档位 E.
标杆: server/model/response/chat_message.py

约定:
  - 仅保留 {Entity}GetListResponse, 字段 List 为 list[{Entity}] ORM
  - GET 列表: return {Entity}GetListResponse(List=service.get_list(...).data)
  - POST / PATCH: status_code=200, 无 response body
"""

from __future__ import annotations

from pydantic import ConfigDict
from sqlmodel import SQLModel

from server.model.{entity} import {Entity}


class {Entity}GetListResponse(SQLModel):
    """GET /{entities} 响应."""

    model_config = ConfigDict(from_attributes=True)

    List: list[{Entity}]
