"""共享环境变量加载。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_DATABASE_URL = "postgresql+asyncpg://billmind:billmind@localhost:5432/billmind"
_DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
_DEFAULT_WEB_ORIGINS = (
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)
_CONFIG_LOADED = False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _config_path() -> Path:
    explicit = os.getenv("BILLMIND_CONFIG", "").strip()
    if explicit:
        return Path(explicit)
    return _repo_root() / "config.yaml"


def _yaml_value_to_env(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


def load_config() -> None:
    global _CONFIG_LOADED
    if _CONFIG_LOADED:
        return

    path = _config_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"未找到配置文件: {path}\n"
            f"请复制 config.yaml.example 为 config.yaml 并填入所需密钥。"
        )

    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    if not isinstance(data, dict):
        raise ValueError(f"配置文件格式无效（应为 YAML 映射）: {path}")

    for key, value in data.items():
        if value is None:
            continue
        env_key = str(key).upper()
        if env_key in os.environ:
            continue
        os.environ[env_key] = _yaml_value_to_env(value)

    _CONFIG_LOADED = True


load_env = load_config


def get_database_url() -> str:
    load_config()
    return os.getenv("DATABASE_URL", _DEFAULT_DATABASE_URL)


def get_api_base_url() -> str:
    """BillMind REST API 根地址，供 agent tools 与集成测试复用。"""
    load_config()
    return os.getenv("API_BASE_URL", _DEFAULT_API_BASE_URL).rstrip("/")


def get_web_origins() -> list[str]:
    """Web 开发源，供 CORSMiddleware 使用。``WEB_ORIGIN`` 可逗号分隔多个。"""
    load_config()
    if custom := os.getenv("WEB_ORIGIN") or os.getenv("FRONTEND_ORIGIN"):
        return [stripped for origin in custom.split(",") if (stripped := origin.strip())]
    return list(_DEFAULT_WEB_ORIGINS)


def get_amap_api_key() -> str | None:
    """高德 MCP API Key；未配置时返回 None（便于 skip 测试）。"""
    load_config()
    value = os.getenv("AMAP_MAPS_API_KEY", "").strip()
    return value or None


def get_geo_default_ip() -> str | None:
    """本地/调试固定 IP；未配置时返回 None，由请求解析用户真实 IP。"""
    load_config()
    value = os.getenv("GEO_DEFAULT_IP", "").strip()
    return value or None


def get_milvus_uri() -> str:
    """Milvus gRPC/HTTP 地址，供 RAG 向量库使用。"""
    load_config()
    return os.getenv("MILVUS_URI", "http://127.0.0.1:19530").strip()


def get_ollama_embedding_model() -> str:
    """Ollama embedding 模型名。"""
    load_config()
    return os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text").strip()


def get_ollama_base_url() -> str:
    """Ollama OpenAI 兼容 /v1 地址，供 Chat 使用。"""
    load_config()
    explicit = os.getenv("OLLAMA_BASE_URL", "").strip()
    if explicit:
        return explicit
    uri = os.getenv("OLLAMA_URI", "").strip().rstrip("/")
    if uri:
        return f"{uri}/v1"
    return "http://localhost:11434/v1"


def get_ollama_vision_model() -> str:
    load_config()
    return os.getenv("OLLAMA_VISION_MODEL", "qwen2.5vl:7b").strip()


def get_ollama_text_model() -> str:
    load_config()
    return os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:7b").strip()


def is_deepseek_use_system_proxy() -> bool:
    load_config()
    return os.getenv("DEEPSEEK_USE_SYSTEM_PROXY", "").lower() in ("1", "true", "yes")


def get_deepseek_model() -> str:
    """DeepSeek Chat 模型 ID（默认 ``deepseek-v4-flash``）。"""
    load_config()
    return os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash").strip()


def is_deepseek_thinking_disabled() -> bool:
    """DeepSeek V4 是否关闭 Thinking（``thinking.type=disabled``，默认 true）。

    ``DEEPSEEK_REASONING_EFFORT=low/medium/high`` 仍会产出 reasoning_tokens，Agent 路径一律视为关闭。
    仅 ``DEEPSEEK_THINKING_DISABLED=false`` 或 ``DEEPSEEK_REASONING_EFFORT=enabled`` 时开启。
    见 ``docs/knowledge/M11.1-slim-prompt-reasoning-latency.md``。
    """
    load_config()
    effort = os.getenv("DEEPSEEK_REASONING_EFFORT", "").strip().lower()
    if effort in ("enabled", "on", "true", "1"):
        return False
    if os.getenv("DEEPSEEK_THINKING_DISABLED", "").strip().lower() in ("0", "false", "no", "off"):
        return False
    return True


def get_deepseek_reasoning_effort() -> str:
    """Thinking 开启时传给 API 的 ``reasoning_effort``（默认 ``high``，可选 ``max``）。"""
    load_config()
    raw = os.getenv("DEEPSEEK_REASONING_EFFORT", "high").strip().lower()
    if raw in ("enabled", "on", "true", "1", ""):
        return "high"
    if raw in ("max", "high"):
        return raw
    # DeepSeek 文档：low/medium 在 thinking 模式下映射为 high
    if raw in ("low", "medium"):
        return "high"
    return raw


def get_checkpointer_pool_max() -> int:
    """AsyncPostgresSaver 连接池 ``max_size``（默认 5）。"""
    load_config()
    raw = os.getenv("CHECKPOINTER_POOL_MAX", "5").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 5


def get_ollama_uri() -> str:
    """Ollama 原生 API 根地址（Embedding 等，非 Chat 用的 OpenAI 兼容 /v1）。

    优先读 ``OLLAMA_URI``；未配置时从 ``OLLAMA_BASE_URL`` 去掉 ``/v1`` 后缀推导。
    """
    load_config()
    explicit = os.getenv("OLLAMA_URI", "").strip().rstrip("/")
    if explicit:
        return explicit
    raw = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").strip().rstrip("/")
    return raw[:-3] if raw.endswith("/v1") else raw


def get_rag_top_k() -> int:
    load_config()
    raw = os.getenv("RAG_TOP_K", "4").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 4


def get_milvus_health_uri() -> str:
    """Milvus standalone 健康检查地址（由 ``MILVUS_URI`` 主机 + ``:9091/healthz`` 推导）。"""
    load_config()
    explicit = os.getenv("MILVUS_HEALTH_URI", "").strip().rstrip("/")
    if explicit:
        return explicit
    uri = os.getenv("MILVUS_URI", "").strip().rstrip("/")
    if not uri or "://" not in uri:
        raise ValueError("请在 config.yaml 配置 milvus_uri 或 milvus_health_uri")
    scheme, rest = uri.split("://", 1)
    host = rest.split("/", 1)[0].split(":", 1)[0]
    return f"{scheme}://{host}:9091/healthz"


def _env_flag(name: str, *, default: bool = True) -> bool:
    load_config()
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def is_txn_search_incremental_enabled() -> bool:
    """记账/导入后是否自动 upsert 交易向量（``TXN_SEARCH_INCREMENTAL``，默认开启）。"""
    return _env_flag("TXN_SEARCH_INCREMENTAL", default=True)


def get_intent_embedding_threshold() -> float:
    """意图嵌入阈值（``INTENT_EMBEDDING_THRESHOLD``，默认 0.7)。

    Returns:
        float: 意图嵌入阈值
    """
    load_config()
    raw = os.getenv("INTENT_EMBEDDING_THRESHOLD", "0.7").strip()
    try:
        return float(raw)
    except ValueError:
        return 0.7


def get_intent_bert_threshold() -> float:
    """意图 BERT 阈值（``INTENT_BERT_THRESHOLD``，默认 0.8)。

    Returns:
        float: 意图 BERT 阈值
    """
    load_config()
    raw = os.getenv("INTENT_BERT_THRESHOLD", "0.8").strip()
    try:
        return float(raw)
    except ValueError:
        return 0.8

def configure_langsmith() -> None:
    """按 LangSmith Quickstart 同步 ``LANGSMITH_*`` 到进程环境，供 LangGraph 自动 trace。"""
    load_config()
    tracing_raw = os.getenv("LANGSMITH_TRACING", "").strip().lower()
    if tracing_raw in {"true", "1", "yes", "on"}:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    elif tracing_raw in {"false", "0", "no", "off"}:
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"

    for key in ("LANGSMITH_ENDPOINT", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT"):
        if value := os.getenv(key, "").strip():
            os.environ[key] = value


_LANGSMITH_API_TO_UI: dict[str, str] = {
    "https://api.smith.langchain.com": "https://smith.langchain.com",   # 美国 endpoint
    "https://eu.api.smith.langchain.com": "https://eu.smith.langchain.com",   # 欧洲 endpoint
    "https://apac.api.smith.langchain.com": "https://apac.smith.langchain.com",   # 亚太 endpoint
    "https://aws.api.smith.langchain.com": "https://aws.smith.langchain.com",   # AWS endpoint
}


def is_langsmith_tracing_enabled() -> bool:
    """``LANGSMITH_TRACING`` 是否为开启状态。"""
    load_config()
    return os.getenv("LANGSMITH_TRACING", "").strip().lower() in {"true", "1", "yes", "on"}


def get_langsmith_project() -> str | None:
    load_config()
    value = os.getenv("LANGSMITH_PROJECT", "").strip()
    return value or None


def get_langsmith_ui_url() -> str | None:
    """由 ``LANGSMITH_ENDPOINT`` 推导 LangSmith 后台 Web 控制台地址；tracing 未开时返回 None。"""
    if not is_langsmith_tracing_enabled():
        return None
    load_config()
    api = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com").strip().rstrip("/")
    if ui := _LANGSMITH_API_TO_UI.get(api):
        return ui
    if ".api.smith.langchain.com" in api:
        return api.replace(".api.smith", ".smith", 1)
    return "https://smith.langchain.com"
