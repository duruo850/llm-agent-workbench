"""LangChain @tool 共用 JSON 序列化。"""

from __future__ import annotations

import json
from typing import Any


def format_tool_result(data: Any) -> str:
    if hasattr(data, "model_dump"):
        payload = data.model_dump(mode="json")
    elif isinstance(data, list):
        payload = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in data
        ]
    else:
        payload = data
    return json.dumps(payload, ensure_ascii=False, default=str)


def format_db_error(exc: Exception) -> str:
    return json.dumps({"error": True, "detail": str(exc)}, ensure_ascii=False)
