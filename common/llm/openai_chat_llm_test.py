"""DeepSeek ChatOpenAI 工厂 — reasoning_effort 等。"""

from __future__ import annotations

import pytest

from common.llm.openai_chat_llm import get_openai_chat_llm
from common.llm.types import LLMCapability, LLMProvider


@pytest.fixture(autouse=True)
def _deepseek_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")


def test_deepseek_uses_low_reasoning_effort_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_REASONING_EFFORT", raising=False)
    monkeypatch.delenv("DEEPSEEK_THINKING_DISABLED", raising=False)
    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        check_health=False,
    )
    assert llm.reasoning_effort == "low"
    assert llm.model_kwargs == {}


def test_deepseek_reasoning_effort_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_REASONING_EFFORT", "medium")
    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        check_health=False,
    )
    assert llm.reasoning_effort == "medium"
    assert llm.model_kwargs == {}


def test_deepseek_can_omit_reasoning_effort(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_REASONING_EFFORT", "none")
    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        check_health=False,
    )
    assert llm.reasoning_effort is None
    assert llm.model_kwargs == {}
