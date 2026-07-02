from typing import Any
from agent.common.text import tool_result_text
import json

def is_no_tool_result(output: Any) -> bool:
    """判断工具返回是否视为「无结果」（与 prompt 规则、streak 逻辑对齐）。

    视为无结果的情况：
    - 空字符串 / 纯空白
    - 字面量 ``{}`` / ``[]``
    - JSON 对象含 ``error`` 字段
    - 非 JSON 但文本中含 ``error``（大小写不敏感）
    """
    text = tool_result_text(output).strip()
    if not text or text in ("{}", "[]"):
        return True
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return '"error"' in text.lower()
    return (isinstance(parsed, dict) and "error" in parsed) or parsed in ({}, [])