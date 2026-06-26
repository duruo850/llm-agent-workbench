"""Bearer token 解析纯函数单测。"""

from __future__ import annotations

import pytest

from utils.bearer_token import parse_bearer_token


def test_parse_bearer_token_ok() -> None:
    assert parse_bearer_token("Bearer abc123") == "abc123"


def test_parse_bearer_token_missing() -> None:
    with pytest.raises(ValueError, match="missing or invalid"):
        parse_bearer_token(None)


def test_parse_bearer_token_empty() -> None:
    with pytest.raises(ValueError, match="empty bearer token"):
        parse_bearer_token("Bearer ")


def test_parse_bearer_token_bad_prefix() -> None:
    with pytest.raises(ValueError, match="missing or invalid"):
        parse_bearer_token("Basic abc")
