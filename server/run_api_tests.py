#!/usr/bin/env python3
"""一键运行 server/api HTTP 集成测试。

用法（仓库根目录）::

    .venv/bin/python3.14 server/run_api_tests.py

若 API 未启动，会自动后台拉起 ``server/main.py``，轮询 ``/health`` 通过后执行
``pytest server/api -v``。默认测试结束后保持 API 运行。

选项::

    --stop-api    测试结束后关闭本脚本启动的 API 进程
    --no-start    不自动启动 API（未运行时直接失败）
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".venv" / "bin" / "python3.14"
API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
HEALTH_URL = f"{API_BASE}/health"
HEALTH_TIMEOUT_SEC = 120


def _check_health() -> bool:
    try:
        response = httpx.get(HEALTH_URL, timeout=3.0)
        return response.status_code == 200
    except Exception:
        return False


def _wait_health() -> bool:
    deadline = time.monotonic() + HEALTH_TIMEOUT_SEC
    while time.monotonic() < deadline:
        if _check_health():
            return True
        time.sleep(0.5)
    return False


def _start_api() -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [str(PYTHON), "server/main.py"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 server/api 全部 HTTP 集成测试")
    parser.add_argument(
        "--stop-api",
        action="store_true",
        help="测试结束后关闭由本脚本启动的 API",
    )
    parser.add_argument(
        "--no-start",
        action="store_true",
        help="不自动启动 API（未运行则退出）",
    )
    args, pytest_args = parser.parse_known_args()
    if not pytest_args:
        pytest_args = ["-v"]

    if not PYTHON.is_file():
        print(f"未找到 Python: {PYTHON}", file=sys.stderr)
        return 1

    api_proc: subprocess.Popen[bytes] | None = None
    started_by_script = False

    if not _check_health():
        if args.no_start:
            print(
                f"API 未运行 ({HEALTH_URL})，请先执行: {PYTHON} server/main.py",
                file=sys.stderr,
            )
            return 1
        print(f"API 未运行，正在启动 {PYTHON} server/main.py ...")
        api_proc = _start_api()
        started_by_script = True
        if not _wait_health():
            if api_proc.poll() is None:
                api_proc.terminate()
            print(f"API 在 {HEALTH_TIMEOUT_SEC}s 内未就绪: {HEALTH_URL}", file=sys.stderr)
            return 1
        print("API 已就绪。")
    else:
        print(f"API 已在运行: {HEALTH_URL}")

    cmd = [str(PYTHON), "-m", "pytest", "server/api", *pytest_args]
    print("执行:", " ".join(cmd))

    import pytest

    os.chdir(ROOT)
    exit_code = pytest.main(["server/api", *pytest_args])

    if started_by_script and args.stop_api and api_proc is not None:
        api_proc.terminate()
        try:
            api_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_proc.kill()
        print("已关闭本脚本启动的 API。")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
