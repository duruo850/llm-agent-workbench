"""Ollama 本地视觉模型 LangChain 封装。"""

from langchain_openai import ChatOpenAI

from src.common.llm.factory import OLLAMA_BASE_URL, OLLAMA_VISION_MODEL, check_ollama_health
from src.common.llm import LLMCapability, LLMProvider, get_langchain_chat_llm

__all__ = ["OLLAMA_BASE_URL", "OLLAMA_VISION_MODEL", "get_ollama_vision_llm"]


def get_ollama_vision_llm(temperature: float = 0, *, check_health: bool = True) -> ChatOpenAI:
    """基于 Ollama 配置创建支持视觉输入的 ChatOpenAI 实例。

    Args:
        temperature: 采样温度，解析任务默认 0。
        check_health: 启动前是否检查 Ollama 服务可达。

    Returns:
        配置好 model、base_url 的 ChatOpenAI 实例（OpenAI 兼容 /v1 接口）。
    """
    if check_health:
        check_ollama_health()
    return get_langchain_chat_llm(
        provider=LLMProvider.OLLAMA,
        capability=LLMCapability.VISION,
        temperature=temperature,
    )
