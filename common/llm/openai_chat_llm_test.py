"""DeepSeek ChatOpenAI 工厂 — thinking 开关等。"""

from __future__ import annotations

import os

import pytest

from common.llm.openai_chat_llm import get_openai_chat_llm
from common.llm.types import LLMCapability, LLMProvider


@pytest.fixture(autouse=True)
def _deepseek_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")


def test_deepseek_disables_thinking_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_THINKING_DISABLED", raising=False)
    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        check_health=False,
    )
    assert llm.model_kwargs == {"thinking": {"type": "disabled"}}


def test_deepseek_can_enable_thinking(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_THINKING_DISABLED", "false")
    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        check_health=False,
    )
    assert llm.model_kwargs == {}
