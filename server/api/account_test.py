"""Account API 集成测试 — register / login / guest / Bearer 401。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import httpx

from common.test.account import bearer_headers, login, register


def test_guest_login(http_client_no_auth: httpx.Client) -> None:
    response = http_client_no_auth.post("/accounts/login", json={"guest": True})
    assert response.status_code == 200
    body = response.json()
    assert body["token"]
    assert body["name"].startswith("guest_")
    assert isinstance(body["account_id"], int)

    again = http_client_no_auth.post("/accounts/login", json={"guest": True}).json()
    assert again["token"] != body["token"]
    assert again["account_id"] != body["account_id"]


def test_register_and_login(http_client_no_auth: httpx.Client, unique_suffix: str) -> None:
    name = f"account-{unique_suffix}"
    password = "secret-1"
    body = register(http_client_no_auth, name, password)
    assert body["name"] == name
    assert body["token"]
    assert "password" not in body
    assert "password_hash" not in body

    again = http_client_no_auth.post(
        "/accounts/register",
        json={"name": name, "password": password},
    )
    assert again.status_code == 409

    logged = login(http_client_no_auth, name, password)
    assert logged["name"] == name
    assert logged["token"] != body["token"]

    # 注册后立刻用同一密码登录（不经过 register helper 的 409 分支）
    direct = http_client_no_auth.post(
        "/accounts/login",
        json={"name": name, "password": password},
    )
    assert direct.status_code == 200, direct.text
    assert direct.json()["name"] == name
    assert direct.json()["token"]


def test_register_then_login_exact_password(
    http_client_no_auth: httpx.Client, unique_suffix: str
) -> None:
    """复现：注册指定密码后，原密码可登录，错误密码 401。"""
    name = f"test-{unique_suffix}"
    password = "123456"

    reg = http_client_no_auth.post(
        "/accounts/register",
        json={"name": name, "password": password},
    )
    assert reg.status_code == 200, reg.text
    reg_body = reg.json()
    assert reg_body["name"] == name
    assert reg_body["token"]
    assert isinstance(reg_body["account_id"], int)

    bad = http_client_no_auth.post(
        "/accounts/login",
        json={"name": name, "password": "wrong-password"},
    )
    assert bad.status_code == 401

    ok = http_client_no_auth.post(
        "/accounts/login",
        json={"name": name, "password": password},
    )
    assert ok.status_code == 200, ok.text
    ok_body = ok.json()
    assert ok_body["name"] == name
    assert ok_body["account_id"] == reg_body["account_id"]
    assert ok_body["token"] != reg_body["token"]


def test_login_wrong_password(http_client_no_auth: httpx.Client, unique_suffix: str) -> None:
    name = f"wrong-pw-{unique_suffix}"
    register(http_client_no_auth, name, "right-pass")
    response = http_client_no_auth.post(
        "/accounts/login",
        json={"name": name, "password": "bad-pass"},
    )
    assert response.status_code == 401


def test_duplicate_login_refreshes_token(
    http_client_no_auth: httpx.Client, unique_suffix: str
) -> None:
    name = f"relogin-{unique_suffix}"
    token1 = login(http_client_no_auth, name)["token"]
    token2 = login(http_client_no_auth, name)["token"]

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
    token_b = login(http_client_no_auth, f"account-b-{unique_suffix}")["token"]

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
