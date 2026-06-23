"""DeepSeek Model Adapter。

统一模型调用层：把 client.chat.completions.create(...)
封装成 generate() → EvalResult。不直接依赖 deepseek_client，
由调用方注入 client_functor（通常为 get_client）。
"""

import time
from collections.abc import Callable
from dataclasses import dataclass

from openai import OpenAI

DEFAULT_MODEL = "deepseek-chat"


@dataclass
class EvalResult:
    """单次模型调用的结构化结果。"""

    output: str
    latency_ms: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    error: str | None = None


class DeepSeekAdapter:
    """DeepSeek 的 Model Adapter。

    换 GPT/Claude 时新增 Adapter 并注入对应 client_functor 即可。
    """

    def __init__(
        self,
        client_functor: Callable[[], OpenAI],
        model: str = DEFAULT_MODEL,
    ):
        self.model = model
        self._client: OpenAI = client_functor()

    def generate(
        self,
        prompt: str,
        temperature: float = 0,
        system: str | None = None,
        max_tokens: int | None = None,
    ) -> EvalResult:
        """调用模型生成一次回答，返回 EvalResult。"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        start = time.time()
        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        resp = self._client.chat.completions.create(**kwargs)
        latency_ms = (time.time() - start) * 1000
        usage = resp.usage
        return EvalResult(
            output=resp.choices[0].message.content or "",
            latency_ms=latency_ms,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )
