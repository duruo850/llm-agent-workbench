"""LangChain ChatOpenAI 封装，复用 DeepSeek 配置。"""

import os

from langchain_openai import ChatOpenAI

from src.common.deepseek_client import BASE_URL, MODEL


def get_chat_llm(temperature: float = 0) -> ChatOpenAI:
    """基于 DeepSeek 配置创建 LangChain ChatOpenAI 实例。

    Args:
        temperature: 采样温度，解析任务默认 0 以保证输出稳定。

    Returns:
        配置好 model、api_key、base_url 的 ChatOpenAI 实例。

    Raises:
        ValueError: 未设置 DEEPSEEK_API_KEY 时抛出，并提示复制 .env.example。
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "未找到 DEEPSEEK_API_KEY。请复制 .env.example 为 .env 并填入 API Key。"
        )
    return ChatOpenAI(
        model=MODEL,
        api_key=api_key,
        base_url=BASE_URL,
        temperature=temperature,
    )
