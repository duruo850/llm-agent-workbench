"""Day 1 / M0：LangChain 记账意图解析链。

本示例演示 LangChain 三个核心抽象如何协作：

1. **Model（模型）** — `ChatOpenAI` 封装 LLM 调用，通过 `get_chat_llm()` 复用 DeepSeek 配置。
2. **Prompt Template（提示词模板）** — `ChatPromptTemplate` 将用户输入 `{text}` 嵌入固定指令，
   并附带 few-shot 示例，引导模型稳定输出 JSON。
3. **Chain（链）** — LCEL 的 `|` 运算符将 Prompt → LLM → StrOutputParser 串联成一条可复用管道。

数据流：用户自然语言 → PromptTemplate → ChatOpenAI → JSON 字符串 → json.loads → ParsedTransaction
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from pydantic import Field

# 将项目根目录加入 sys.path，使 `from src.common ...` 在直接运行脚本时可用
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda

from src.common.langchain_llm import get_chat_llm

# ---------------------------------------------------------------------------
# 结构化输出：解析后的记账记录
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = ("amount", "category", "merchant", "note")


@dataclass
class ParsedTransaction:
    """LLM 解析后的记账记录。"""

    amount: float = Field(description="金额，收入为正数，支出也为正数（由 category 区分收支）")
    category: str = Field(description="分类，如「餐饮」「交通」「工资」「购物」等；无法判断时用「其他」")
    merchant: str = Field(description="商户或来源，如 Starbucks、地铁、盒马；无法判断时用空字符串")
    note: str = Field(description="补充说明，没有则用空字符串")


# ---------------------------------------------------------------------------
# Prompt 设计：要求只输出 JSON，并嵌入 few-shot 提升格式稳定性
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
你是一个个人记账助手。从用户的自然语言输入中提取记账信息，只输出 JSON，不要任何额外文字。

字段说明：
- amount (float): 金额，收入为正数，支出也为正数（由 category 区分收支）
- category (str): 分类，如「餐饮」「交通」「工资」「购物」等；无法判断时用「其他」
- merchant (str): 商户或来源，如 Starbucks、地铁、盒马；无法判断时用空字符串
- note (str): 补充说明，没有则用空字符串

示例：
输入：刚才 Starbucks 花了 38，算餐饮
输出：{{"amount": 38.0, "category": "餐饮", "merchant": "Starbucks", "note": ""}}

输入：收到工资 15000
输出：{{"amount": 15000.0, "category": "工资", "merchant": "", "note": "工资收入"}}
"""

_USER_TEMPLATE = "输入：{text}\n输出："


def _format_message(item: object, index: int, total: int) -> str:
    """格式化单条消息，多行 content 缩进显示，避免与下一条消息混淆。"""
    cls_name = type(item).__name__
    role = getattr(item, "type", "?")
    content = getattr(item, "content", item)
    header = f"── 消息 {index}/{total}: {cls_name} (role={role}) ──"
    body = "\n".join(f"  {line}" for line in str(content).splitlines())
    return f"{header}\n{body}"


def _format_message_list(items: list) -> str:
    total = len(items)
    return "\n".join(_format_message(item, i, total) for i, item in enumerate(items, start=1))


def _extract_messages(value: object) -> list | None:
    """从 ChatPromptValue、消息列表或单条 Message 中提取消息列表。"""
    messages = getattr(value, "messages", None)
    if messages is not None:
        return list(messages)
    if isinstance(value, list):
        return value
    if getattr(value, "content", None) is not None and hasattr(value, "type"):
        return [value]
    return None


def _format_log_value(value: object) -> str:
    """将链各阶段的值格式化为可读字符串，便于打印日志。"""
    type_name = type(value).__name__

    if isinstance(value, dict):
        return f"类型: {type_name}\n{json.dumps(value, ensure_ascii=False, indent=2)}"

    if isinstance(value, str):
        return f"类型: {type_name}\n{value}"

    messages = _extract_messages(value)
    return (
        f"类型: {type_name}（共 {len(messages)} 条消息，非单段文本）\n{_format_message_list(messages)}"
        if messages is not None
        else f"类型: {type_name}\n{value!s}"
    )


def _print_logged_value(label: str, value: object) -> None:
    print(f"    {label}:")
    for line in _format_log_value(value).splitlines():
        print(f"      {line}")


def _log_stage_io(stage_name: str, input_value: object, output_value: object) -> None:
    """打印某一 Runnable 阶段的 input 与 output。"""
    print(f"\n  ▸ {stage_name}")
    _print_logged_value("input", input_value)
    _print_logged_value("output", output_value)


def _trace_runnable(stage_name: str, runnable: Runnable) -> RunnableLambda:
    """包装 Runnable：invoke 前后打印该阶段的 input / output。"""
    def run(input_value: object) -> object:
        output_value = runnable.invoke(input_value)
        _log_stage_io(stage_name, input_value, output_value)
        return output_value

    return RunnableLambda(run)


def build_parse_chain(verbose: bool = False):
    """组装 LCEL 链：ChatPromptTemplate | ChatOpenAI | StrOutputParser。

    Chain 概念：`|` 运算符将上一步的返回值传入下一步 `invoke()`，
    但每步都会对数据做转换/加工，并非原样透传。
    """
    # Prompt Template：system 消息放指令 + few-shot，human 消息放用户输入
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", _USER_TEMPLATE),
        ]
    )

    # Model：temperature=0 保证解析结果稳定、可复现
    llm = get_chat_llm(temperature=0)
    parser = StrOutputParser()

    if not verbose:
        return prompt | llm | parser

    # verbose：每步 invoke 时打印 input / output（每步都会转换数据形态，二者不全等）
    return (
        _trace_runnable("1. Prompt（dict → system + human 消息列表）", prompt)
        | _trace_runnable("2. LLM（基于消息上下文生成新 AIMessage）", llm)
        | _trace_runnable("3. Parser（从 AIMessage 提取 content 字符串）", parser)
    )


def _validate_fields(data: dict) -> ParsedTransaction:
    """校验 LLM 返回的 JSON 是否包含所需字段且类型正确。"""
    if missing := [f for f in REQUIRED_FIELDS if f not in data]:
        raise ValueError(f"JSON 缺少字段: {missing}")

    amount = data["amount"]
    if not isinstance(amount, (int, float)):
        raise ValueError(f"amount 应为数字，实际为 {type(amount).__name__}")

    return ParsedTransaction(
        amount=float(amount),
        category=str(data["category"]),
        merchant=str(data["merchant"]),
        note=str(data["note"]) if data["note"] is not None else "",
    )


def parse_transaction(text: str, verbose: bool = False) -> ParsedTransaction:
    """调用 chain 解析单条自然语言记账语句。

    Args:
        text: 用户输入，如「刚才 Starbucks 花了 38，算餐饮」。

    Returns:
        校验通过的 ParsedTransaction。

    Raises:
        ValueError: JSON 解析失败或字段校验不通过。
    """
    chain = build_parse_chain(verbose=verbose)

    # LCEL：`invoke` 时上一步返回值会传入下一步，但每步都会转换数据：
    #   Prompt: dict → 消息列表；LLM: 消息列表 → 新 AIMessage；Parser: 提取 content 字符串
    raw_output = chain.invoke({"text": text})

    # 去除可能的 markdown 代码块包裹（```json ... ```）
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

    return _validate_fields(data)


# ---------------------------------------------------------------------------
# 内置测试用例
# ---------------------------------------------------------------------------

TEST_CASES = [
    "刚才 Starbucks 花了 38，算餐饮",
    "地铁 6 块，交通",
    "收到工资 15000",
    "在盒马买了水果牛奶一共 89.5 元",
]


def main() -> None:
    """运行 4 条内置测试语句并打印解析结果。"""
    print("=" * 60)
    print("M0 记账意图解析链 — LangChain LCEL Demo")
    print("=" * 60)

    success_count = 0
    for i, text in enumerate(TEST_CASES, start=1):
        print(f"\n[{i}] 输入: {text}")
        try:
            result = parse_transaction(text, verbose=True)
            print(f"    输出: {result}")
            success_count += 1
        except ValueError as exc:
            print(f"    失败: {exc}")

    print(f"\n{'=' * 60}")
    print(f"解析成功: {success_count}/{len(TEST_CASES)}")
    if success_count < 3:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        # API Key 缺失等配置错误
        print(f"配置错误: {exc}", file=sys.stderr)
        sys.exit(1)
