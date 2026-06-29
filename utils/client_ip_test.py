"""客户端 IP 解析单测。"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / "pytest.ini").is_file())))

import pytest

from utils.client_ip import get_client_ip


def _request(*, host: str = "127.0.0.1", forwarded: str | None = None) -> MagicMock:
    request = MagicMock()
    request.headers.get.return_value = forwarded
    request.client.host = host
    return request


def test_get_client_ip_query_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEO_DEFAULT_IP", raising=False)
    assert get_client_ip(_request(), override="1.2.3.4") == "1.2.3.4"


def test_get_client_ip_env_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEO_DEFAULT_IP", "112.48.54.75")
    assert get_client_ip(_request(host="10.0.0.1")) == "112.48.54.75"


def test_get_client_ip_from_request(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEO_DEFAULT_IP", raising=False)
    assert get_client_ip(_request(host="203.0.113.9")) == "203.0.113.9"


def test_get_client_ip_forwarded_for(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEO_DEFAULT_IP", raising=False)
    assert get_client_ip(_request(forwarded="198.51.100.2, 10.0.0.1")) == "198.51.100.2"
