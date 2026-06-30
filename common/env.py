"""共享环境变量加载。"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_DEFAULT_DATABASE_URL = "postgresql+asyncpg://billmind:billmind@localhost:5432/billmind"
_DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
_DEFAULT_WEB_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)
_ENV_LOADED = False


def load_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    root = Path(__file__).resolve().parents[1]
    load_dotenv(root / ".env")
    _ENV_LOADED = True


def get_database_url() -> str:
    load_env()
    return os.getenv("DATABASE_URL", _DEFAULT_DATABASE_URL)


def get_api_base_url() -> str:
    """BillMind REST API 根地址，供 agent tools 与集成测试复用。"""
    load_env()
    return os.getenv("API_BASE_URL", _DEFAULT_API_BASE_URL).rstrip("/")


def get_web_origins() -> list[str]:
    """Web 开发源，供 CORSMiddleware 使用。``WEB_ORIGIN`` 可逗号分隔多个。"""
    load_env()
    if custom := os.getenv("WEB_ORIGIN") or os.getenv("FRONTEND_ORIGIN"):
        return [stripped for origin in custom.split(",") if (stripped := origin.strip())]
    return list(_DEFAULT_WEB_ORIGINS)


def get_amap_api_key() -> str | None:
    """高德 MCP API Key；未配置时返回 None（便于 skip 测试）。"""
    load_env()
    value = os.getenv("AMAP_MAPS_API_KEY", "").strip()
    return value or None


def get_geo_default_ip() -> str | None:
    """本地/调试固定 IP；未配置时返回 None，由请求解析用户真实 IP。"""
    load_env()
    value = os.getenv("GEO_DEFAULT_IP", "").strip()
    return value or None


def get_milvus_uri() -> str:
    """Milvus gRPC/HTTP 地址，供 RAG 向量库使用。"""
    load_env()
    return os.getenv("MILVUS_URI", "http://127.0.0.1:19530").strip()


def get_ollama_embedding_model() -> str:
    """Ollama embedding 模型名。"""
    load_env()
    return os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text").strip()


def get_ollama_uri() -> str:
    """Ollama 原生 API 根地址（Embedding 等，非 Chat 用的 OpenAI 兼容 /v1）。

    优先读 ``OLLAMA_URI``；未配置时从 ``OLLAMA_BASE_URL`` 去掉 ``/v1`` 后缀推导。
    """
    load_env()
    explicit = os.getenv("OLLAMA_URI", "").strip().rstrip("/")
    if explicit:
        return explicit
    raw = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").strip().rstrip("/")
    return raw[:-3] if raw.endswith("/v1") else raw


def get_rag_top_k() -> int:
    load_env()
    raw = os.getenv("RAG_TOP_K", "4").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 4
