"""LLM 输出格式化：清理常见包裹格式并解析为结构化数据。"""

from __future__ import annotations

import json


def format_json(raw_output: str) -> dict:
    """将 LLM 原始 JSON 字符串格式化为 dict。

    会 strip 首尾空白、去掉 markdown 代码块（`` ```json ... ``` ``），再 ``json.loads``。

    Args:
        raw_output: LLM 原始输出。示例：
            ``'{"amount": 38.0, "category": "餐饮", "merchant": "Starbucks", "note": ""}'``
            或带代码块：
            ``'```json\\n{"amount": 38.0, "category": "餐饮", "merchant": "Starbucks", "note": ""}\\n```'``

    Returns:
        解析后的 dict。示例：
            ``{"amount": 38.0, "category": "餐饮", "merchant": "Starbucks", "note": ""}``
    """
    cleaned = raw_output.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 解析失败，原始输出：\n{raw_output}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"期望 JSON 对象，实际为 {type(data).__name__}")

    return data
