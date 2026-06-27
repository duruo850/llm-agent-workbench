"""测试资源路径。"""

from __future__ import annotations

from pathlib import Path

RESOURCE_DIR = Path(__file__).resolve().parent / "resource"


def resource_path(name: str) -> Path:
    return RESOURCE_DIR / name
