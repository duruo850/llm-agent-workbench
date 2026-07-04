"""集成测试专用常量与 helper — 不进入主进程 config / env。"""

from __future__ import annotations

import time

CONVERSATION_WRITE_SETTLE_SECONDS = 5.0


def wait_conversation_write_settle() -> None:
    """异步 conversation 落库后，等待 DB 可见再断言。"""
    time.sleep(CONVERSATION_WRITE_SETTLE_SECONDS)
