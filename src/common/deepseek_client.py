"""DeepSeek API 统一客户端封装。

供示例与 DeepSeekAdapter(client_functor=get_client) 使用。
配置：项目根目录 `.env` 中的 DEEPSEEK_API_KEY。
"""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import OpenAI

MODEL = "deepseek-chat"
BASE_URL = "https://api.deepseek.com"

_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)


def _use_system_proxy() -> bool:
    """是否使用系统代理（SOCKS/HTTP）。

    终端有 all_proxy 时需设 DEEPSEEK_USE_SYSTEM_PROXY=1；
    默认 trust_env=False，避免无 socks 支持时连不上 API。
    """
    return os.getenv("DEEPSEEK_USE_SYSTEM_PROXY", "").lower() in ("1", "true", "yes")


def get_client() -> OpenAI:
    """创建 OpenAI 兼容的 DeepSeek 客户端。

    Returns:
        配置好 api_key、base_url 的 OpenAI 实例。

    Raises:
        ValueError: 未设置 DEEPSEEK_API_KEY 时抛出，并提示复制 .env.example。
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "未找到 DEEPSEEK_API_KEY。请复制 .env.example 为 .env 并填入 API Key。"
        )
    http_client = None if _use_system_proxy() else httpx.Client(trust_env=False)
    return OpenAI(api_key=api_key, base_url=BASE_URL, http_client=http_client)
