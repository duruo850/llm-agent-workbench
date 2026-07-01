"""HTTP 集成测试共用 fixture（与 API 路由同目录）。

需先手动启动 API（``python server/main.py``），再运行::

    pytest server/api -v

单独调试某个文件（须先启动 API）::

    pytest server/api/categories_test.py -v
    pytest server/api/categories_test.py::test_get_category -v

Cursor：打开测试文件 → **Debug pytest (current file)**。
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from typing import Any

import httpx
import pytest

from common.env import load_env
from common.test.account import login_token

DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
TEST_MONTH = "2025-06"


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
def require_llm() -> None:
    load_env()
    if not os.getenv("DEEPSEEK_API_KEY"):
        pytest.skip("未配置 DEEPSEEK_API_KEY，跳过 Agent 集成测试")


@pytest.fixture
def require_amap() -> None:
    load_env()
    if not os.getenv("AMAP_MAPS_API_KEY"):
        pytest.skip("未配置 AMAP_MAPS_API_KEY，跳过高德 MCP 集成测试")


@pytest.fixture
def require_rag() -> None:
    from agent.rag.knowledge import Knowledge
    from common.milvus import embedding_ready

    load_env()
    if not embedding_ready():
        pytest.skip("Milvus 不可用，跳过 RAG 集成测试")
    try:
        Knowledge.index(force=False)
    except Exception as exc:
        pytest.skip(f"RAG 索引不可用: {exc}")


@pytest.fixture
def require_graph_backend() -> None:
    try:
        import langgraph  # noqa: F401
    except ImportError:
        pytest.skip("未安装 langgraph，跳过 LangGraph 集成测试")


@pytest.fixture
def http_client_no_auth(
    require_api: str, api_base_url: str
) -> Generator[httpx.Client, None, None]:
    with httpx.Client(base_url=api_base_url, timeout=15.0) as client:
        yield client


@pytest.fixture
def auth_token(http_client_no_auth: httpx.Client, unique_suffix: str) -> str:
    return login_token(http_client_no_auth, f"test-{unique_suffix}")


@pytest.fixture
def http_client(
    require_api: str,
    api_base_url: str,
    auth_token: str,
) -> Generator[httpx.Client, None, None]:
    with httpx.Client(
        base_url=api_base_url,
        timeout=15.0,
        headers={"Authorization": f"Bearer {auth_token}"},
    ) as client:
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
