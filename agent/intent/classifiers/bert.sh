#!/usr/bin/env bash
# 训练 M12 意图 BERT（sklearn）分类器，输出到本目录 sklearn_pipeline.joblib
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/../../.." && pwd)"
cd "$ROOT"

PYTHON="${PYTHON:-$ROOT/.venv/bin/python3.14}"
TRAIN="$ROOT/scripts/train_intent_classifier.py"
OUTPUT="$DIR/sklearn_pipeline.joblib"

if [[ ! -x "$PYTHON" ]]; then
  echo "错误: 未找到 Python: $PYTHON" >&2
  echo "请先创建虚拟环境并安装依赖: pip install -r requirements.txt" >&2
  exit 1
fi

if [[ ! -f "$TRAIN" ]]; then
  echo "错误: 训练脚本不存在: $TRAIN" >&2
  exit 1
fi

echo "训练意图分类器 (sklearn) ..."
echo "  python: $PYTHON"
echo "  输出:   $OUTPUT"
"$PYTHON" "$TRAIN" --output "$DIR"

if [[ ! -f "$OUTPUT" ]]; then
  echo "错误: 训练完成但未找到 $OUTPUT" >&2
  exit 1
fi

echo "完成: $OUTPUT"
