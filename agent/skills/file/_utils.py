"""文件类 skill 共用工具。"""

from __future__ import annotations

import json


def skill_reply_to_text(raw: str) -> str:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    if isinstance(payload, dict) and payload.get("message"):
        return str(payload["message"])
    return raw
