"""Bearer Authorization header 解析（与 HTTP 框架无关）。"""

from __future__ import annotations

BEARER_PREFIX = "Bearer "


def parse_bearer_token(authorization: str | None) -> str:
    """从 Authorization header 提取 token；缺失或格式非法时抛 ValueError。"""
    if authorization and authorization.startswith(BEARER_PREFIX):
        if token := authorization[len(BEARER_PREFIX) :].strip():
            return token
        raise ValueError("empty bearer token")
    raise ValueError("missing or invalid Authorization header")
