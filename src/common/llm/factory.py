"""LangChain ChatOpenAI 统一工厂：按平台 + 能力路由到 DeepSeek / Ollama。"""

from __future__ import annotations

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.common.llm.types import LLMCapability, LLMProvider, ProviderSpec

_env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(_env_path)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:7b")
OLLAMA_TEXT_MODEL = os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b")


def _use_system_proxy() -> bool:
    return os.getenv("DEEPSEEK_USE_SYSTEM_PROXY", "").lower() in ("1", "true", "yes")


def _resolve_spec(
    provider: LLMProvider,
    capability: LLMCapability,
) -> ProviderSpec:
    if provider is LLMProvider.DEEPSEEK:
        from src.common.deepseek_client import BASE_URL, MODEL

        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError(
                "未找到 DEEPSEEK_API_KEY。请复制 .env.example 为 .env 并填入 API Key。"
            )
        if capability is LLMCapability.VISION:
            raise ValueError("DeepSeek deepseek-chat 不支持视觉输入，请使用 Ollama 视觉模型。")
        return ProviderSpec(
            provider=provider,
            capability=capability,
            model=MODEL,
            base_url=BASE_URL,
            api_key=api_key,
        )

    if provider is LLMProvider.OLLAMA:
        model = OLLAMA_VISION_MODEL if capability is LLMCapability.VISION else OLLAMA_TEXT_MODEL
        return ProviderSpec(
            provider=provider,
            capability=capability,
            model=model,
            base_url=OLLAMA_BASE_URL,
            api_key="ollama",
        )

    raise ValueError(f"未知 Provider: {provider}")


def get_langchain_chat_llm(
    provider: LLMProvider = LLMProvider.DEEPSEEK,
    capability: LLMCapability = LLMCapability.TEXT,
    temperature: float = 0,
) -> ChatOpenAI:
    """按平台与能力创建 LangChain ChatOpenAI 实例。

    所有 Provider 均走 OpenAI 兼容接口，LangChain 侧统一为 ChatOpenAI。
    """
    spec = _resolve_spec(provider, capability)

    kwargs: dict = {
        "model": spec.model,
        "api_key": spec.api_key,
        "base_url": spec.base_url,
        "temperature": temperature,
    }

    if spec.provider is LLMProvider.DEEPSEEK and not _use_system_proxy():
        kwargs["http_client"] = httpx.Client(trust_env=False)

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
