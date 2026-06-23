"""DeepSeek API 公共模块。"""

from src.common.deepseek_adapter import DEFAULT_MODEL, DeepSeekAdapter, EvalResult
from src.common.deepseek_client import BASE_URL, MODEL, get_client

__all__ = [
    "BASE_URL",
    "DEFAULT_MODEL",
    "DeepSeekAdapter",
    "EvalResult",
    "MODEL",
    "get_client",
]
