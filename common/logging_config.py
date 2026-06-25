"""应用日志配置 — 只保留 billmind.* 业务日志，压低第三方库噪音。"""

from __future__ import annotations

import logging

_NOISY_LOGGERS = (
    "httpx",
    "httpcore",
    "langchain_openai",
    "openai",
)


def configure_app_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.ERROR)
