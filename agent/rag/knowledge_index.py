"""一键入库 CLI — 启动 RAG 依赖并将 agent/knowledge 索引到 Milvus。

用法::

    .venv/bin/python3.14 -m agent.rag.index

配置见下方常量 ``SKIP_DOCKER``、``INDEX_FORCE``、``KNOWLEDGE_ROOT``、``KNOWLEDGE_DIRS``。
"""

from __future__ import annotations

import subprocess
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

_REPO_ROOT = Path(__file__).resolve().parents[2]
_COMPOSE_FILE = _REPO_ROOT / "docker-compose.yml"
_DOCKER_SERVICES = ("ollama", "etcd", "minio", "milvus")

# 一键入库配置
SKIP_DOCKER = False
INDEX_FORCE = True
KNOWLEDGE_ROOT = Path(__file__).resolve().parents[1] / "knowledge"
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
    raise SystemExit(
        f"错误: 缺少 {model}，请检查: docker compose -f {_COMPOSE_FILE} logs ollama"
    )


def _ensure_docker_services() -> None:
    cmd = [
        "docker", "compose", "-f", str(_COMPOSE_FILE),
        "up", "-d", *_DOCKER_SERVICES,
    ]
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def _print_plan() -> None:
    load_env()
    model = get_ollama_embedding_model()
    tags_url = f"{get_ollama_uri().rstrip('/')}/api/tags"
    health_url = get_milvus_health_uri()
    print("\n== BillMind RAG 一键入库 ==\n\n将执行:\n")
    if SKIP_DOCKER:
        print("  # 跳过 docker compose")
    else:
        print(f"  docker compose -f {_COMPOSE_FILE} up -d {' '.join(_DOCKER_SERVICES)}")
    print(f"  # 等待 Ollama: curl -sf {tags_url} | grep {model}")
    print(f"  # 等待 Milvus: curl -sf {health_url}")
    print(f"  rag.index(force={INDEX_FORCE}, root={KNOWLEDGE_ROOT}, dirs={KNOWLEDGE_DIRS})\n")


def main() -> None:
    _print_plan()

    if not SKIP_DOCKER:
        _ensure_docker_services()

    _wait_ollama_embedding()
    _wait_http("Milvus", get_milvus_health_uri(), attempts=90)

    from agent.rag.knowledge import Knowledge
    from common.milvus import available as milvus_available

    if not milvus_available():
        raise SystemExit("Milvus 不可达，请先 docker compose up -d milvus")

    print(f"+ Knowledge.index(force={INDEX_FORCE}, root={KNOWLEDGE_ROOT}, dirs={KNOWLEDGE_DIRS})")
    count = Knowledge().index(force=INDEX_FORCE, root=KNOWLEDGE_ROOT, dirs=KNOWLEDGE_DIRS)
    print(f"indexed chunks: {count}")


if __name__ == "__main__":
    main()
