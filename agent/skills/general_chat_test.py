"""general_chat skill 单测。"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

from agent.intent.classifiers.rule import RuleClassifier
from agent.skills.general_chat import CANNED_CHAT_REPLIES, reply_general_chat
from agent.skills import init as init_skills
from common.env import get_database_url
from server.db.session import Database


def _fresh_classifier() -> RuleClassifier:
    Database.init(get_database_url())
    init_skills(Database.get().async_session_factory)
    clf = RuleClassifier()
    clf.prepare()
    return clf


def test_reply_general_chat_canned() -> None:
    Database.init(get_database_url())
    init_skills(Database.get().async_session_factory)

    async def _run() -> str:
        async with Database.get().async_session_factory() as db:
            return await reply_general_chat(db, config={"configurable": {"account_id": 1}})

    reply = asyncio.run(_run())
    assert reply in CANNED_CHAT_REPLIES


def test_rule_general_chat() -> None:
    clf = _fresh_classifier()
    result = clf.classify("你好，你能做什么")
    assert result is not None
    assert result.scene == "general_chat"


def test_rule_no_false_positive_on_transaction() -> None:
    clf = _fresh_classifier()
    result = clf.classify("查一下本月餐饮花了多少")
    assert result is not None
    assert result.scene == "transaction"
