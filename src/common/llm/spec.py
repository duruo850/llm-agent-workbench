from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from src.common.llm.types import LLMCapability, LLMProvider, ProviderSpec
from src.common.llm.setting import DEEPSEEK_BASE_URL, DEEPSEEK_MODEL, OLLAMA_BASE_URL, OLLAMA_VISION_MODEL, OLLAMA_TEXT_MODEL

_env_path = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(_env_path)


def resolve_spec(
    provider: LLMProvider,
    capability: LLMCapability,
) -> ProviderSpec:
    """根据提供者与能力，返回 ProviderSpec 实例。"""
    if provider is LLMProvider.DEEPSEEK:
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
            model=DEEPSEEK_MODEL,
            base_url=DEEPSEEK_BASE_URL,
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