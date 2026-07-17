#!/usr/bin/env python3
"""M12 意图分类离线评测 — 准确率 / Top-1 召回 / P99 延迟。

用法::

    .venv/bin/python3.14 test/eval/run_intent_eval.py
    .venv/bin/python3.14 test/eval/run_intent_eval.py --method rule
    .venv/bin/python3.14 test/eval/run_intent_eval.py --method hybrid
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent.intent.manager import IntentManager

CASES_PATH = Path(__file__).with_name("intent_cases.json")


@dataclass
class IntentCaseReport:
    case_id: str
    message: str
    expected_category: str
    actual_category: str
    confidence: float
    method: str
    latency_ms: float
    passed: bool


@dataclass
class IntentEvalReport:
    method: str
    total: int = 0
    correct: int = 0
    cases: list[IntentCaseReport] = field(default_factory=list)
    latencies_ms: list[float] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def top1_recall(self) -> float:
        return self.accuracy

    @property
    def p99_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_lat = sorted(self.latencies_ms)
        idx = min(len(sorted_lat) - 1, int(len(sorted_lat) * 0.99))
        return sorted_lat[idx]


def _bootstrap_manager() -> IntentManager:
    from agent.mcp import MCP_TOOLS, init as init_mcp
    from agent.skills import init as init_skills
    from common.env import get_database_url
    from server.db.session import Database

    try:
        Database.init(get_database_url())
        init_skills(Database.get().async_session_factory)
        import asyncio

        asyncio.run(init_mcp())
    except Exception:
        pass

    from agent.common.skill_registry import skill_registry

    skill_registry.register_skills(MCP_TOOLS, category_id="mcp_gaode")
    manager = IntentManager()
    manager.init()
    return manager


def run_eval(*, method: str, cases_path: Path) -> IntentEvalReport:
    data = json.loads(cases_path.read_text(encoding="utf-8"))
    manager = _bootstrap_manager()

    report = IntentEvalReport(method=method)
    for case in data.get("cases", []):
        message = str(case["message"])
        expected = str(case.get("expected_category") or case.get("expected_scene", ""))
        start = time.perf_counter()
        result = manager.classify(message, method=method)  # type: ignore[arg-type]
        latency_ms = (time.perf_counter() - start) * 1000

        passed = result.scene == expected
        report.total += 1
        if passed:
            report.correct += 1
        report.latencies_ms.append(latency_ms)
        report.cases.append(
            IntentCaseReport(
                case_id=str(case.get("id", "")),
                message=message,
                expected_category=expected,
                actual_category=result.scene,
                confidence=result.confidence,
                method=str(result.method),
                latency_ms=latency_ms,
                passed=passed,
            )
        )
    return report


def print_report(report: IntentEvalReport) -> None:
    print(f"\n=== Intent Eval ({report.method}) ===")
    print(f"accuracy:      {report.accuracy:.1%} ({report.correct}/{report.total})")
    print(f"top-1 recall:  {report.top1_recall:.1%}")
    if report.latencies_ms:
        print(f"latency mean:  {statistics.mean(report.latencies_ms):.1f} ms")
        print(f"latency p99:   {report.p99_latency_ms:.1f} ms")

    failures = [c for c in report.cases if not c.passed]
    if failures:
        print(f"\nFAILURES ({len(failures)}):")
        for item in failures:
            print(
                f"  [{item.case_id}] expected={item.expected_category} "
                f"actual={item.actual_category} ({item.method} {item.confidence:.2f}) "
                f"«{item.message[:40]}»"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="M12 intent classification eval")
    parser.add_argument("--method", default="hybrid", choices=["rule", "embedding", "bert", "hybrid"])
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    parser.add_argument("--min-accuracy", type=float, default=0.90)
    args = parser.parse_args()

    report = run_eval(method=args.method, cases_path=args.cases)
    print_report(report)

    if report.accuracy < args.min_accuracy:
        print(f"\nFAIL: accuracy {report.accuracy:.1%} < {args.min_accuracy:.0%}")
        return 1
    print("\nPASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
