"""测试用 — 获取本机出站公网 IP，并校验高德是否可解析。"""

from __future__ import annotations

import httpx


def fetch_current_public_ip() -> str:
    response = httpx.get("https://api.ipify.org", timeout=10.0)
    response.raise_for_status()
    if not (ip := response.text.strip()):
        raise RuntimeError("无法获取当前公网 IP")
    else:
        return ip

