"""LangChain ChatOpenAI 统一工厂：按平台 + 能力路由到 DeepSeek / Ollama。"""

from __future__ import annotations

import os

import httpx
from langchain_openai import ChatOpenAI

from common.llm.types import LLMCapability, LLMProvider
from common.llm.spec import resolve_spec
from common.llm.setting import OLLAMA_BASE_URL, use_system_proxy

# 避免 langchain-openai 注入自定义 httpx transport 时的代理警告
os.environ.setdefault("LANGCHAIN_OPENAI_TCP_KEEPALIVE", "0")

def get_openai_chat_llm(
    provider: LLMProvider = LLMProvider.DEEPSEEK,
    capability: LLMCapability = LLMCapability.TEXT,
    temperature: float = 0,
    check_health: bool = True
) -> ChatOpenAI:
    """根据提供者与能力，创建 LangChain ChatOpenAI 实例。
    所有 Provider 均走 OpenAI 兼容接口，LangChain 侧统一为 ChatOpenAI。
    """
    spec = resolve_spec(provider, capability)

    kwargs: dict = {
        "model": spec.model,
        "api_key": spec.api_key,
        "base_url": spec.base_url,
        "temperature": temperature,
    }

    if spec.provider is LLMProvider.DEEPSEEK and not use_system_proxy():
        kwargs["http_client"] = httpx.Client(trust_env=False)
        
    if check_health and spec.provider is LLMProvider.OLLAMA:
        check_ollama_health()

    return ChatOpenAI(**kwargs)


def check_ollama_health(base_url: str | None = None) -> None:
    """检查 Ollama 服务是否就绪，未就绪时抛出友好错误。"""
    url = (base_url or OLLAMA_BASE_URL).rstrip("/")
    if url.endswith("/v1"):
        url = url[:-3]
    health_url = f"{url}/"

    try:
        response = httpx.get(health_url, timeout=5.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValueError(
            "Ollama 服务未就绪。请先运行 ./examples/setup-ollama.sh 或 "
            "docker compose -f examples/docker-compose.yml up -d"
        ) from exc
