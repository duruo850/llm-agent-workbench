"""共享环境变量加载。"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_DEFAULT_DATABASE_URL = "postgresql+asyncpg://billmind:billmind@localhost:5432/billmind"
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
