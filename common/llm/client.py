"""OpenAI SDK 统一客户端：DeepSeek / Ollama 均走 OpenAI 兼容 /v1 接口。"""

from __future__ import annotations

import httpx
from openai import OpenAI

from common.llm.openai_chat_llm import _resolve_spec, _use_system_proxy, check_ollama_health
from common.llm.types import LLMCapability, LLMProvider


def get_openai_client(
    provider: LLMProvider = LLMProvider.DEEPSEEK,
    capability: LLMCapability = LLMCapability.TEXT,
    *,
    check_health: bool = True,
) -> OpenAI:
    """按平台与能力创建 OpenAI 兼容客户端。

    DeepSeek 与 Ollama 均暴露 ``/v1/chat/completions``，可直接用
    ``client.chat.completions.create(model=..., messages=...)``。
    默认模型名见 ``factory._resolve_spec`` 返回的 ``ProviderSpec.model``。
    """
    spec = _resolve_spec(provider, capability)

    kwargs: dict = {
        "api_key": spec.api_key,
        "base_url": spec.base_url,
    }
    if spec.provider is LLMProvider.DEEPSEEK and not _use_system_proxy():
        kwargs["http_client"] = httpx.Client(trust_env=False)

    if check_health and spec.provider is LLMProvider.OLLAMA:
        check_ollama_health()

    return OpenAI(**kwargs)
