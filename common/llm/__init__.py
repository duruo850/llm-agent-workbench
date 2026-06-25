"""LLM 平台抽象：DeepSeek / Ollama 统一经 OpenAI 兼容接口对接。"""

from common.llm.formatter import format_json
from common.llm.openai_chat_llm import check_ollama_health, get_openai_chat_llm
from common.llm.openai_client import get_openai_client
from common.llm.setting import (
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_TEXT_MODEL,
    OLLAMA_VISION_MODEL,
)
from common.llm.types import LLMCapability, LLMProvider, ProviderSpec

__all__ = [
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "LLMCapability",
    "LLMProvider",
    "OLLAMA_BASE_URL",
    "OLLAMA_TEXT_MODEL",
    "OLLAMA_VISION_MODEL",
    "ProviderSpec",
    "check_ollama_health",
    "format_json",
    "get_openai_client",
    "get_openai_chat_llm",
]
