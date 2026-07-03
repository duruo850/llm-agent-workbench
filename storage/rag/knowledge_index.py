"""知识库 embedding 入库 — 将 agent/knowledge 索引到 Milvus。

用法::

    python -m storage.rag.knowledge_index

需 Ollama（embedding 模型）与 Milvus 已就绪；地址见 config.yaml。
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from contextlib import suppress
from pathlib import Path

from common.env import (
    get_milvus_health_uri,
    get_ollama_embedding_model,
    get_ollama_uri,
    load_env,
)

INDEX_FORCE = True
KNOWLEDGE_ROOT = Path(__file__).resolve().parents[2] / "agent" / "knowledge"
KNOWLEDGE_DIRS = ("finance",)


def _http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError):
        return False


def _wait_http(name: str, url: str, *, attempts: int = 60, interval: float = 2) -> None:
    print(f"等待 {name}: {url}")
    for _ in range(attempts):
        if _http_ok(url):
            print(f"{name} 已就绪")
            return
        time.sleep(interval)
    raise SystemExit(f"错误: {name} 超时 ({url})")


def _wait_ollama_embedding() -> None:
    load_env()
    model = get_ollama_embedding_model()
    tags_url = f"{get_ollama_uri().rstrip('/')}/api/tags"
    print(f"等待 Ollama embedding 模型: {model} ({tags_url})")
    for _ in range(120):
        with suppress(urllib.error.URLError, TimeoutError):
            with urllib.request.urlopen(tags_url, timeout=5) as resp:
                if model in resp.read().decode():
                    print("embedding 模型已就绪")
                    return
        time.sleep(3)
    raise SystemExit(f"错误: 缺少 embedding 模型 {model}，请确认 Ollama 已启动并已 pull 该模型")


def main() -> None:
    load_env()
    print("\n== BillMind 知识库 embedding 入库 ==\n")
    print(f"  root={KNOWLEDGE_ROOT}, dirs={KNOWLEDGE_DIRS}, force={INDEX_FORCE}\n")

    _wait_ollama_embedding()
    _wait_http("Milvus", get_milvus_health_uri(), attempts=90)

    from common.milvus import available as milvus_available
    from storage.rag.knowledge import Knowledge

    if not milvus_available():
        raise SystemExit("Milvus 不可达，请确认 milvus_uri 配置正确且服务已启动")

    count = Knowledge().index(force=INDEX_FORCE, root=KNOWLEDGE_ROOT, dirs=KNOWLEDGE_DIRS)
    print(f"indexed chunks: {count}")


if __name__ == "__main__":
    main()
