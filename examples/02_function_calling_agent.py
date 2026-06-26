"""M2 Function Calling Agent CLI Demo。

演示 LLM 如何通过 tool_calls 驱动 ``agent/skills`` 直连 PostgreSQL 记一笔与查账。

用法::

    docker compose up -d

    .venv/bin/python examples/02_function_calling_agent.py
    .venv/bin/python examples/02_function_calling_agent.py --repl
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sqlalchemy import text

from common.env import get_database_url
from common.logging_config import configure_app_logging
from agent import Agent
from server.db.session import Database

Database.init(get_database_url())
Agent.init()

DEMO_CASES = [
    "刚才 Starbucks 花了 38，算餐饮",
    "查一下本月餐饮花了多少",
]


async def check_db() -> None:
    try:
        async with Database.get().async_session_factory() as db:
            await db.execute(text("SELECT 1"))
    except Exception as exc:
        print(
            f"PostgreSQL 未就绪: {exc}\n请先运行: docker compose up -d",
            file=sys.stderr,
        )
        sys.exit(1)


async def run_demo(*, debug: bool = False) -> None:
    print("=" * 60)
    print("M2 Function Calling Agent — Demo")
    print("=" * 60)

    async with Database.get().async_session_factory() as db:
        for i, message in enumerate(DEMO_CASES, start=1):
            print(f"\n[{i}] 用户: {message}")
            try:
                reply = (
                    await Agent.invoke(message, db=db, debug=True)
                    if debug
                    else await Agent.invoke(message, db=db)
                )
                print(f"    助手: {reply}")
            except ValueError as exc:
                print(f"    失败: {exc}")


async def run_repl(*, debug: bool = False) -> None:
    print("M2 Agent 交互模式（输入 quit 退出）")
    async with Database.get().async_session_factory() as db:
        while True:
            try:
                message = input("\n你: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not message or message.lower() in {"quit", "exit", "q"}:
                break
            try:
                reply = (
                    await Agent.invoke(message, db=db, debug=True)
                    if debug
                    else await Agent.invoke(message, db=db)
                )
                print(f"助手: {reply}")
            except ValueError as exc:
                print(f"错误: {exc}")


async def async_main(*, repl: bool, debug: bool) -> None:
    await check_db()
    if repl:
        await run_repl(debug=debug)
    else:
        await run_demo(debug=debug)


def main() -> None:
    configure_app_logging()
    parser = argparse.ArgumentParser(description="M2 Function Calling 记账 Agent")
    parser.add_argument("--repl", "--interactive", action="store_true", help="交互模式")
    parser.add_argument("--debug", action="store_true", help="打印 tool 调用链")
    args = parser.parse_args()
    asyncio.run(async_main(repl=args.repl, debug=args.debug))


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"配置错误: {exc}", file=sys.stderr)
        sys.exit(1)
