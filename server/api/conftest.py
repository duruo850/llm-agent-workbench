"""HTTP 集成测试共用 fixture（与 API 路由同目录）。

需先手动启动 API（``python server/main.py``），再运行::

    pytest server/api -v

单独调试某个文件（须先启动 API）::

    pytest server/api/categories_test.py -v
    pytest server/api/categories_test.py::test_get_category -v

Cursor：打开测试文件 → **Debug pytest (current file)**。
"""

from __future__ import annotations

import asyncio
import os
import uuid
from collections.abc import Generator
from typing import Any

import httpx
import pytest

from server.db.session import engine

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
TEST_MONTH = "2025-06"


@pytest.fixture(autouse=True)
def _reset_async_engine_pool() -> None:
    """避免多个 ``asyncio.run`` 测试复用连接池时 event loop 不一致。"""
    yield
    asyncio.run(engine.dispose())


@pytest.fixture(scope="session")
def api_base_url() -> str:
    return os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")


@pytest.fixture(scope="session")
def require_api(api_base_url: str) -> str:
    try:
        response = httpx.get(f"{api_base_url}/health", timeout=3.0)
        response.raise_for_status()
    except Exception as exc:
        pytest.skip(
            f"API 未启动或不可达 ({api_base_url})：{exc}\n"
            "请先运行: python server/main.py"
        )
    return api_base_url


@pytest.fixture
def http_client(require_api: str, api_base_url: str) -> Generator[httpx.Client, None, None]:
    with httpx.Client(base_url=api_base_url, timeout=15.0) as client:
        yield client


@pytest.fixture
def unique_suffix() -> str:
    return uuid.uuid4().hex[:8]


@pytest.fixture
def category(http_client: httpx.Client, unique_suffix: str) -> Generator[dict[str, Any], None, None]:
    name = f"分类-{unique_suffix}"
    response = http_client.post("/categories", json={"name": name, "budget_monthly": 1000})
    response.raise_for_status()
    body = response.json()
    yield body
    http_client.delete(f"/categories/{body['id']}")


@pytest.fixture
def budget(http_client: httpx.Client, category: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
    response = http_client.post(
        "/budgets",
        json={"category_id": category["id"], "month": TEST_MONTH, "limit_amount": 1500},
    )
    response.raise_for_status()
    body = response.json()
    yield body
    http_client.delete(f"/budgets/{body['id']}")


@pytest.fixture
def transaction(
    http_client: httpx.Client,
    category: dict[str, Any],
) -> Generator[dict[str, Any], None, None]:
    response = http_client.post(
        "/transactions",
        json={
            "amount": 38,
            "category": category["name"],
            "merchant": "测试商户",
            "note": "fixture",
            "transacted_at": f"{TEST_MONTH}-25T12:00:00",
        },
    )
    response.raise_for_status()
    body = response.json()
    yield body
    http_client.delete(f"/transactions/{body['id']}")
