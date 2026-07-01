"""Account API 集成测试 — POST /accounts/login 与 Bearer 401。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import httpx

from common.test.account import bearer_headers, login, login_token


def test_login(http_client_no_auth: httpx.Client, unique_suffix: str) -> None:
    name = f"account-{unique_suffix}"
    body = login(http_client_no_auth, name)
    assert body["name"] == name
    assert body["token"]
    assert isinstance(body["account_id"], int)


def test_duplicate_login_refreshes_token(
    http_client_no_auth: httpx.Client, unique_suffix: str
) -> None:
    name = f"relogin-{unique_suffix}"
    token1 = login_token(http_client_no_auth, name)
    token2 = login_token(http_client_no_auth, name)

    assert token2
    assert token2 != token1


def test_no_token_returns_401(http_client_no_auth: httpx.Client) -> None:
    response = http_client_no_auth.get("/categories")
    assert response.status_code == 401


def test_invalid_bearer_returns_401(http_client_no_auth: httpx.Client) -> None:
    response = http_client_no_auth.get(
        "/categories",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401


def test_malformed_authorization_returns_401(http_client_no_auth: httpx.Client) -> None:
    response = http_client_no_auth.get(
        "/categories",
        headers={"Authorization": "Token abc"},
    )
    assert response.status_code == 401


def test_accounts_are_isolated(http_client_no_auth: httpx.Client, unique_suffix: str) -> None:
    """A/B 两账号各自创建的分类互不可见。"""
    account_a = login(http_client_no_auth, f"account-a-{unique_suffix}")
    token_a = account_a["token"]
    token_b = login_token(http_client_no_auth, f"account-b-{unique_suffix}")

    cat_name = f"隔离分类-{unique_suffix}"
    create = http_client_no_auth.post(
        "/categories",
        json={"Data": {"name": cat_name, "account_id": account_a["account_id"]}},
        headers=bearer_headers(token_a),
    )
    create.raise_for_status()
    cat_id = create.json()["id"]

    get_b = http_client_no_auth.get(
        f"/categories/{cat_id}",
        headers=bearer_headers(token_b),
    )
    assert get_b.status_code == 404

    list_b = http_client_no_auth.get(
        "/categories",
        headers=bearer_headers(token_b),
    )
    list_b.raise_for_status()
    assert all(item["name"] != cat_name for item in list_b.json()["List"])

    http_client_no_auth.delete(
        f"/categories/{cat_id}",
        headers=bearer_headers(token_a),
    ).raise_for_status()
