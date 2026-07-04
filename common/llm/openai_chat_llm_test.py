"""DeepSeek ChatOpenAI 工厂 — thinking 开关。"""

from __future__ import annotations

import pytest

from common.llm.openai_chat_llm import get_openai_chat_llm
from common.llm.types import LLMCapability, LLMProvider


@pytest.fixture(autouse=True)
def _deepseek_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")


def test_deepseek_disables_thinking_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_REASONING_EFFORT", raising=False)
    monkeypatch.delenv("DEEPSEEK_THINKING_DISABLED", raising=False)
    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        check_health=False,
    )
    assert llm.extra_body == {"thinking": {"type": "disabled"}}
    from langchain_core.messages import HumanMessage

    payload = llm._get_request_payload([HumanMessage(content="hi")])
    assert payload.get("extra_body") == {"thinking": {"type": "disabled"}}
    assert payload.get("reasoning_effort") is None


def test_deepseek_reasoning_effort_low_still_disables_thinking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEEPSEEK_REASONING_EFFORT", "low")
    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        check_health=False,
    )
    assert llm.extra_body == {"thinking": {"type": "disabled"}}


def test_deepseek_can_enable_thinking(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_THINKING_DISABLED", "false")
    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        check_health=False,
    )
    assert llm.extra_body == {"thinking": {"type": "enabled"}}
    assert llm.reasoning_effort == "high"


def test_deepseek_disabled_does_not_set_reasoning_effort(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DEEPSEEK_REASONING_EFFORT", raising=False)
    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        check_health=False,
    )
    assert llm.reasoning_effort is None
