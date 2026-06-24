#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "错误: 未找到 docker 命令。请先安装 Docker Desktop 并启动。" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "错误: Docker 未运行。请启动 Docker Desktop 后重试。" >&2
  exit 1
fi

if lsof -i :11434 >/dev/null 2>&1; then
  echo "提示: 11434 端口已被占用。若已有 Ollama 在运行可忽略；否则请释放端口后重试。" >&2
fi

echo "启动 Ollama 容器..."
docker compose up -d

echo "等待 Ollama 就绪..."
for i in $(seq 1 60); do
  if docker compose exec -T ollama ollama list >/dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "错误: Ollama 启动超时。请检查: docker compose logs" >&2
    exit 1
  fi
  sleep 2
done

MODEL="${OLLAMA_VISION_MODEL:-qwen2.5vl:7b}"
echo "拉取视觉模型 ${MODEL}（首次约 6GB，请耐心等待）..."
if ! docker compose exec -T ollama ollama pull "${MODEL}"; then
  echo "错误: 模型 pull 失败。请检查网络或磁盘空间。" >&2
  exit 1
fi

echo ""
echo "完成。运行图片入账示例:"
echo "  .venv/bin/python examples/01_image_ollama_chain/01_image_ollama_chain.py"
