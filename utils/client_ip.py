"""从 FastAPI Request 提取客户端 IP。"""

from __future__ import annotations

from fastapi import Request

from common.env import get_geo_default_ip


def get_client_ip(request: Request, *, override: str | None = None) -> str:
    """优先 query override，其次 GEO_DEFAULT_IP，再 X-Forwarded-For / request.client.host。"""
    if override:
        return override.strip()

    if default_ip := get_geo_default_ip():
        return default_ip

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first

    if request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"
