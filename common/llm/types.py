"""LLM 平台与能力枚举，供 factory 路由不同 Provider。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LLMProvider(str, Enum):
    """模型平台：决定 base_url、api_key 来源与默认模型。"""

    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"


class LLMCapability(str, Enum):
    """模型能力：文本对话或视觉多模态。"""

    TEXT = "text" # 文本对话
    VISION = "vision" # 视觉多模态


@dataclass(frozen=True)
class ProviderSpec:
    """单个 Provider 的运行时配置。"""

    provider: LLMProvider # 模型平台
    capability: LLMCapability # 模型能力
    model: str # 模型名称   
    base_url: str # 模型基础URL
    api_key: str # 模型API密钥
