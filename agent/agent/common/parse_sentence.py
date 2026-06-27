"""自然语言单句 → 是否账单 + 记账字段（CSV 逐行导入等共用）。"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from agent.agent.promt.parse_sentence import (
    SENTENCE_PARSE_SYSTEM_PROMPT,
    SENTENCE_PARSE_USER_TEMPLATE,
)
from common.llm import LLMCapability, LLMProvider, format_json, get_openai_chat_llm
from server.model.request.parsed import LoadTransaction, ParsedTransaction

_parse_chain: Runnable | None = None


def _get_parse_chain() -> Runnable:
    global _parse_chain
    if _parse_chain is None:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SENTENCE_PARSE_SYSTEM_PROMPT),
                ("human", SENTENCE_PARSE_USER_TEMPLATE),
            ]
        )
        llm = get_openai_chat_llm(
            provider=LLMProvider.DEEPSEEK,
            capability=LLMCapability.TEXT,
            temperature=0,
        )
        _parse_chain = prompt | llm | StrOutputParser()
    return _parse_chain


@dataclass
class SentenceParseResult:
    is_transaction: bool
    transaction: ParsedTransaction | None = None


def load_sentence_parse(raw: str | dict) -> SentenceParseResult:
    data = format_json(raw) if isinstance(raw, str) else raw
    if not data.get("is_transaction"):
        return SentenceParseResult(is_transaction=False)
    return SentenceParseResult(
        is_transaction=True,
        transaction=LoadTransaction(data),
    )


async def parse_sentence(text: str) -> SentenceParseResult:
    """解析单句：账单则带 ParsedTransaction，否则 is_transaction=False。"""
    chain = _get_parse_chain()
    raw_output = await chain.ainvoke({"text": text})
    return load_sentence_parse(raw_output)
