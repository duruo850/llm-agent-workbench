#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
TAG="${1:-latest}"

for target in server web; do
  echo "==> billmind-${target}:${TAG}"
  docker build -f "${target}/Dockerfile" . \
    --build-arg "APP_VERSION=${TAG}" \
    --tag "billmind-${target}:${TAG}"
done

echo "done: billmind-server:${TAG}, billmind-web:${TAG}"
