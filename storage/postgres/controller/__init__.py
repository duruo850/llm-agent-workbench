"""PostgreSQL 后台 Controller — 异步落库队列等。"""

from __future__ import annotations

from storage.postgres.controller.conversation.controller import conversation_controller


def init_controllers() -> None:
    conversation_controller.start()


def shutdown_controllers() -> None:
    conversation_controller.shutdown()
