from typing import Any
import logging

logger = logging.getLogger(__name__)


def extract_token_usage(event: dict[str, Any]) -> int:
    """从 ``on_chat_model_end`` 事件提取 token 合计（prompt + completion）。

    优先读 AIMessage.usage_metadata;兼容 response_metadata.token_usage。
    模型或代理未返回 metadata 时记 0 并打 WARN,不中断主流程。
    """
    output = event.get("data", {}).get("output")
    if output is None:
        logger.warning("on_chat_model_end missing output, token_usage=0")
        return 0

    usage = getattr(output, "usage_metadata", None) or {}
    if isinstance(usage, dict):
        total = usage.get("total_tokens")
        if total is not None:
            return int(total)
        prompt = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
        completion = int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
        if prompt or completion:
            return prompt + completion

    response_meta = getattr(output, "response_metadata", None) or {}
    if isinstance(response_meta, dict):
        token_usage = response_meta.get("token_usage")
        if isinstance(token_usage, dict):
            total = token_usage.get("total_tokens")
            if total is not None:
                return int(total)

    logger.warning("on_chat_model_end without usage metadata, token_usage=0")
    return 0
