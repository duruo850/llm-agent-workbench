#!/usr/bin/env python3
"""BillMind 离线 Agent Eval CLI(M11)

测试机制
--------
本脚本在**当前 Python 进程内**完成评测，与 ``POST /agent/chat`` 走同一套 Agent 代码路径，
启动 agent server 但**不启动** ``server/main.py``、**不经过** FastAPI / HTTP。

流程概览::

    docker compose up -d          # PostgreSQL(skills 记一笔 / 查账需要)
    .env 含 DEEPSEEK_API_KEY      # 真实 LLM;可选 LANGSMITH_* 做 trace

    Database.init + init_agent()  # 与 server lifespan 相同:storage / skills / MCP / graph
    login_or_register("eval-runner")
    对 test_cases.json 每条用例:
        Agent.invoke(message, ...)   # LangGraph ainvoke,非 HTTP
        scorers 打分（工具链 + 回复关键词）
    打印 PASS/FAIL 报告

与 server/api/agent_test.py 的区别：集成测试要起 HTTP 客户端；这里直接 ``Agent.invoke``。

用法::

    .venv/bin/python3.14 test/eval/run_eval.py
    .venv/bin/python3.14 test/eval/run_eval.py --limit 3
    .venv/bin/python3.14 test/eval/run_eval.py --llm-judge   # 需用例含 llm_judge 字段

先跑纯逻辑单测（不调 LLM）::

    .venv/bin/python3.14 -m pytest test/eval/scorers_test.py -v
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from agent import Agent, init_agent, shutdown_agent
from common.env import configure_langsmith, get_database_url
from common.logging_config import configure_app_logging
from server.db.session import Database
from storage.postgres.service import account_service
from utils.agent.eval.scorers import ScoreResult, aggregate_scores, score_llm_judge, score_reply_keywords, score_tools
from common.test.db import check_db

EVAL_ACCOUNT_NAME = "eval-runner"
CASES_PATH = Path(__file__).with_name("test_cases.json")


@dataclass
class CaseReport:
    """单条用例的执行与打分结果。"""

    case_id: str
    message: str
    reply: str
    actual_tools: list[str]
    scores: list[ScoreResult] = field(default_factory=list)
    aggregate: ScoreResult | None = None
    error: str | None = None


async def _run_case(
    db,
    account_id: int,
    case: dict,
    *,
    use_llm_judge: bool,
) -> CaseReport:
    """跑一条用例：进程内 invoke → 提取工具链 → scorers 打分。"""
    del db  # invoke 不强制需要 session；账号 id 已在外部 login 取得
    case_id = str(case["id"])
    message = str(case["message"])
    thread_id = f"eval-{case_id}"  # 每条用例独立 thread，避免 checkpointer 串话

    try:
        # 与 HTTP /agent/chat 相同入口：Agent.invoke（LangGraph ainvoke）
        reply, _, tool_names = await Agent.invoke(
            message,
            account_id=account_id,
            thread_id=thread_id,
        )

        scores: list[ScoreResult] = [
            score_tools(
                tool_names,
                case.get("expected_tools"),
                match=case.get("tool_match", "all"),
                forbidden_tools=case.get("forbidden_tools"),
            ),
            score_reply_keywords(
                reply,
                case.get("reply_keywords"),
                match_all=case.get("reply_match_all", True),
            ),
        ]
        if use_llm_judge and case.get("llm_judge"):
            scores.append(await score_llm_judge(reply, str(case["llm_judge"])))

        aggregate = aggregate_scores(scores)
        return CaseReport(
            case_id=case_id,
            message=message,
            reply=reply,
            actual_tools=tool_names,
            scores=scores,
            aggregate=aggregate,
        )
    except Exception as exc:
        return CaseReport(
            case_id=case_id,
            message=message,
            reply="",
            actual_tools=[],
            error=str(exc),
        )


def _load_cases(limit: int | None) -> list[dict]:
    """读取 test_cases.json；支持 ``{"cases": [...]}`` 或纯数组（兼容旧格式）。"""
    payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    cases = payload["cases"] if isinstance(payload, dict) else payload
    return cases[:limit] if limit is not None else cases

def _print_report(reports: list[CaseReport]) -> int:
    """stdout 人类可读报告；全部 PASS 时 exit 0，否则 1。"""
    passed = 0
    total = len(reports)
    print("=" * 72)
    print(f"BillMind Eval — invoke (in-process, no HTTP) cases={total}")
    print("=" * 72)

    for report in reports:
        if report.error:
            status = "ERROR"
            print(f"\n[{report.case_id}] {status}")
            print(f"  message: {report.message}")
            print(f"  error: {report.error}")
            continue

        assert report.aggregate is not None
        ok = report.aggregate.passed
        if ok:
            passed += 1
        status = "PASS" if ok else "FAIL"
        print(f"\n[{report.case_id}] {status} score={report.aggregate.score:.2f}")
        print(f"  message: {report.message}")
        print(f"  tools: {report.actual_tools}")
        print(f"  reply: {report.reply[:160]}{'…' if len(report.reply) > 160 else ''}")
        for score in report.scores:
            mark = "ok" if score.passed else "fail"
            print(f"  - {score.name} ({mark}, {score.score:.2f}): {score.detail}")

    rate = (passed / total * 100) if total else 0.0
    print("\n" + "=" * 72)
    print(f"Summary: {passed}/{total} passed ({rate:.1f}%)")
    print("=" * 72)
    return 0 if passed == total else 1


async def main_async(*, limit: int | None, use_llm_judge: bool) -> int:
    configure_app_logging()
    configure_langsmith()  # 可选；LANGSMITH_TRACING=true 时 LangGraph 自动上报
    await check_db(Database.get().async_session_factory())

    Database.init(get_database_url())
    await init_agent()  # storage → skills → MCP → Agent.init()，等同 server lifespan
    try:
        cases = _load_cases(limit)
        async with Database.get().async_session_factory() as db:
            account = await account_service.login_or_register(db, EVAL_ACCOUNT_NAME)
            reports = [
                await _run_case(db, account.id, case, use_llm_judge=use_llm_judge)
                for case in cases
            ]
        return _print_report(reports)
    finally:
        await shutdown_agent()


def main() -> None:
    limit = None # 只跑前 N 条用例
    use_llm_judge = False # 对配置了 llm_judge 的用例启用 LLM-as-judge
    raise SystemExit(asyncio.run(main_async(limit=limit, use_llm_judge=use_llm_judge)))


if __name__ == "__main__":
    main()
