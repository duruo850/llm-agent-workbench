"""M12 前置意图识别 — ``intent_manager`` 为唯一入口。"""

from agent.intent.manager import (
    IntentCandidate,
    IntentManager,
    IntentResult,
    intent_manager,
)

__all__ = [
    "IntentCandidate",
    "IntentManager",
    "IntentResult",
    "intent_manager",
]

def init() -> None:
    """初始化意图分类器。"""
    intent_manager.init()