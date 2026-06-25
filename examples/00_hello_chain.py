"""Day 1 / M0：LangChain 记账意图解析链。

本示例演示 LangChain 三个核心抽象如何协作：

2. **Prompt Template（提示词模板）** — `ChatPromptTemplate` 将用户输入 `{text}` 嵌入固定指令，
   并附带 few-shot 示例，引导模型稳定输出 JSON。
3. **Chain（链）** — LCEL 的 `|` 运算符将 Prompt → LLM → StrOutputParser 串联成一条可复用管道。

数据流：用户自然语言 → PromptTemplate → ChatOpenAI → JSON 字符串 → json.loads → ParsedTransaction
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from examples.common.chain_debug import trace_runnable
from src.common.llm import LLMCapability, LLMProvider, format_json, get_openai_chat_llm
from src.model.Transaction import Transaction, LoadTransaction

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


def build_parse_chain(verbose: bool = False):
    """组装 LCEL 链：ChatPromptTemplate | ChatOpenAI | StrOutputParser。"""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", _USER_TEMPLATE),
        ]
    )

    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        temperature=0,
    )
    parser = StrOutputParser()

    if not verbose:
        return prompt | llm | parser

    return (
        trace_runnable("1. Prompt（dict → system + human 消息列表）", prompt)
        | trace_runnable("2. LLM（基于消息上下文生成新 AIMessage）", llm)
        | trace_runnable("3. Parser（从 AIMessage 提取 content 字符串）", parser)
    )


def parse_transaction(text: str, verbose: bool = False) -> Transaction:
    """调用 chain 解析单条自然语言记账语句。"""
    chain = build_parse_chain(verbose=verbose)
    raw_output = chain.invoke({"text": text})
    return LoadTransaction(raw_output)


TEST_CASES = [
    "刚才 Starbucks 花了 38，算餐饮",
    "地铁 6 块，交通",
    "收到工资 15000",
    "在盒马买了水果牛奶一共 89.5 元",
]


def main() -> None:
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


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"配置错误: {exc}", file=sys.stderr)
        sys.exit(1)
