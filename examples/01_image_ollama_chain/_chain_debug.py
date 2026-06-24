"""LCEL 链 verbose 调试工具，供 examples 复用。"""

from __future__ import annotations

import json

from langchain_core.runnables import Runnable, RunnableLambda


def _summarize_image_url(text: str) -> str:
    if "data:image/" in text and ";base64," in text:
        prefix, _, b64 = text.partition(";base64,")
        mime = prefix.replace("data:", "")
        kb = len(b64) * 3 // 4 // 1024
        return f"[{mime}, ~{kb} KB, base64_len={len(b64)}]"
    return text


def _summarize_for_log(value: object) -> object:
    """递归缩短日志中的 base64 / data URL，避免刷屏。"""
    if isinstance(value, str):
        return _summarize_image_url(value)
    if isinstance(value, dict):
        summarized: dict = {}
        for key, item in value.items():
            if key in ("image_url", "url") and isinstance(item, str):
                summarized[key] = _summarize_image_url(item)
            elif key == "image_url" and isinstance(item, dict) and isinstance(item.get("url"), str):
                summarized[key] = {"url": _summarize_image_url(item["url"])}
            else:
                summarized[key] = _summarize_for_log(item)
        return summarized
    if isinstance(value, list):
        return [_summarize_for_log(item) for item in value]
    return value


def _format_message(item: object, index: int, total: int) -> str:
    cls_name = type(item).__name__
    role = getattr(item, "type", "?")
    content = getattr(item, "content", item)
    header = f"── 消息 {index}/{total}: {cls_name} (role={role}) ──"
    display = _summarize_for_log(content)
    body = "\n".join(f"  {line}" for line in str(display).splitlines())
    return f"{header}\n{body}"


def _format_message_list(items: list) -> str:
    total = len(items)
    return "\n".join(_format_message(item, i, total) for i, item in enumerate(items, start=1))


def _extract_messages(value: object) -> list | None:
    messages = getattr(value, "messages", None)
    if messages is not None:
        return list(messages)
    if isinstance(value, list):
        return value
    if getattr(value, "content", None) is not None and hasattr(value, "type"):
        return [value]
    return None


def format_log_value(value: object) -> str:
    """将链各阶段的值格式化为可读字符串，便于打印日志。"""
    type_name = type(value).__name__

    if isinstance(value, dict):
        display = _summarize_for_log(value)
        return f"类型: {type_name}\n{json.dumps(display, ensure_ascii=False, indent=2)}"

    if isinstance(value, str):
        return f"类型: {type_name}\n{_summarize_image_url(value)}"

    messages = _extract_messages(value)
    return (
        f"类型: {type_name}（共 {len(messages)} 条消息，非单段文本）\n{_format_message_list(messages)}"
        if messages is not None
        else f"类型: {type_name}\n{value!s}"
    )


def _print_logged_value(label: str, value: object) -> None:
    print(f"    {label}:")
    for line in format_log_value(value).splitlines():
        print(f"      {line}")


def log_stage_io(stage_name: str, input_value: object, output_value: object) -> None:
    print(f"\n  ▸ {stage_name}")
    _print_logged_value("input", input_value)
    _print_logged_value("output", output_value)


def trace_runnable(stage_name: str, runnable: Runnable) -> RunnableLambda:
    """包装 Runnable：invoke 前后打印该阶段的 input / output。"""

    def run(input_value: object) -> object:
        output_value = runnable.invoke(input_value)
        log_stage_io(stage_name, input_value, output_value)
        return output_value

    return RunnableLambda(run)
