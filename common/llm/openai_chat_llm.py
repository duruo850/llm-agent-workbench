"""LangChain ChatOpenAI 统一工厂：按平台 + 能力路由到 DeepSeek / Ollama。"""

from __future__ import annotations

import os

import httpx
from langchain_openai import ChatOpenAI

from common.env import get_deepseek_reasoning_effort, is_deepseek_thinking_disabled
from common.llm.types import LLMCapability, LLMProvider
from common.llm.spec import resolve_spec
from common.llm.setting import OLLAMA_BASE_URL, use_system_proxy

# 避免 langchain-openai 注入自定义 httpx transport 时的代理警告
os.environ.setdefault("LANGCHAIN_OPENAI_TCP_KEEPALIVE", "0")

def get_openai_chat_llm(
    provider: LLMProvider = LLMProvider.DEEPSEEK,
    capability: LLMCapability = LLMCapability.TEXT,
    temperature: float = 0,
    check_health: bool = True,
) -> ChatOpenAI:
    """根据提供者与能力，创建 LangChain ChatOpenAI 实例。

    所有 Provider 均走 OpenAI 兼容接口；DeepSeek 在构造时注入 ``extra_body.thinking``，
    每次 ``invoke`` / ``ainvoke`` 由 LangChain 自动带入请求，无需调用方再设。
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

    # 设置DeepSeek的extra_body
    if spec.provider is LLMProvider.DEEPSEEK:
        # DeepSeek 官方：thinking 走 extra_body；开启时另传顶层 reasoning_effort
        # https://api-docs.deepseek.com/guides/thinking_mode
        if is_deepseek_thinking_disabled():
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
        else:
            kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
            kwargs["reasoning_effort"] = get_deepseek_reasoning_effort()

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
            "Ollama 服务未就绪。请先运行 ./examples/01_image_ollama_chain/setup-ollama.sh 或 "
            "docker compose up -d ollama"
        ) from exc
