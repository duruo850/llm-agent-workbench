"""LLM 平台抽象：DeepSeek / Ollama 统一经 LangChain ChatOpenAI 对接。"""

from src.common.llm.factory import (
    OLLAMA_BASE_URL,
    OLLAMA_VISION_MODEL,
    check_ollama_health,
    get_langchain_chat_llm,
)
from src.common.llm.types import LLMCapability, LLMProvider, ProviderSpec

__all__ = [
    "LLMCapability",
    "LLMProvider",
    "OLLAMA_BASE_URL",
    "OLLAMA_VISION_MODEL",
    "ProviderSpec",
    "check_ollama_health",
    "get_langchain_chat_llm",
]
