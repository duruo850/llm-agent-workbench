"""Day 1 扩展：Ollama 视觉模型 + 截图入账 LCEL 链。

数据流：支付截图 → base64 data URL → Multimodal Prompt → Ollama qwen2.5vl → JSON → ParsedTransaction

前置：./examples/setup-ollama.sh（Docker 启动 Ollama 并 pull qwen2.5vl:7b）
"""

from __future__ import annotations

import base64
import mimetypes
import sys
from pathlib import Path

# 脚本在 examples/01_image_ollama_chain/ 下，需向上 3 层到项目根（含 src/）
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from examples.common.chain_debug import trace_runnable
from common.llm import LLMCapability, LLMProvider, get_openai_chat_llm
from common.llm import LLMCapability, LLMProvider, format_json, get_openai_chat_llm
from server.model.request.parsed import Transaction, LoadTransaction

_IMAGE_SYSTEM_PROMPT = """\
你是一个个人记账助手。从微信/支付宝等支付或转账截图中提取记账信息，只输出 JSON，不要任何额外文字。

字段说明：
- amount (float): 金额绝对值（截图中的 -20 应输出20 ）
- category (str): 分类，如「餐饮」「交通」「转账」「购物」等；无法判断时用「其他」
- merchant (str): 收款方/商户/对方昵称；转账场景取收款人名称
- note (str): 转账说明、备注等；没有则用空字符串

示例（微信转账截图）：
输出：{{"amount": 20.0, "category": "转账", "merchant": "baby", "note": "冰棒"}}
"""

_DEFAULT_IMAGE = Path(__file__).resolve().parent / "weixinpay01.jpg"


def _encode_image(path: Path) -> str:
    """读取图片并返回 data URL（供 LangChain image_url 使用）。"""
    if not path.is_file():
        raise FileNotFoundError(f"图片不存在: {path}")

    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "image/jpeg"
    raw = path.read_bytes()
    b64 = base64.standard_b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def build_image_parse_chain(verbose: bool = False):
    """组装 multimodal LCEL 链：Prompt | Ollama Vision LLM | StrOutputParser。"""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _IMAGE_SYSTEM_PROMPT),
            (
                "human",
                [
                    {"type": "text", "text": "请从这张支付/转账截图提取记账 JSON。"},
                    {"type": "image_url", "image_url": {"url": "{image_url}"}},
                ],
            ),
        ]
    )

    llm = get_openai_chat_llm(
        provider=LLMProvider.OLLAMA,
        capability=LLMCapability.VISION,
        temperature=0,
    )
    parser = StrOutputParser()

    if not verbose:
        return prompt | llm | parser

    return (
        trace_runnable("1. Prompt（dict → system + human 多模态消息）", prompt)
        | trace_runnable("2. Ollama Vision LLM（图片 + 文本 → AIMessage）", llm)
        | trace_runnable("3. Parser（从 AIMessage 提取 content 字符串）", parser)
    )


def parse_transaction_from_image(
    path: Path | str,
    verbose: bool = False,
) -> Transaction:
    """从支付/转账截图解析记账记录。"""
    image_path = Path(path)
    print("image_path:", image_path)
    image_binary = _encode_image(image_path)
    print("image_binar,len(str):", len(image_binary))
    chain = build_image_parse_chain(verbose=verbose)
    print("chain invoke start!!", chain)  
    raw_output = chain.invoke({"image_url": image_binary})
    print("chain invoke end!! raw_output:", raw_output)
    return LoadTransaction(raw_output)


def main() -> None:
    image_path = _DEFAULT_IMAGE
    print("=" * 60)
    print("图片入账 — Ollama qwen2.5vl + LangChain LCEL")
    print("=" * 60)
    print(f"\n图片: {image_path.name}")
    print("（Intel Mac CPU 推理可能需 30s+，请耐心等待）\n")

    try:
        result = parse_transaction_from_image(image_path, verbose=True)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\n解析结果: {result}")

    if result.amount != 3000.0:
        print(f"警告: amount 期望 3000.0，实际 {result.amount}", file=sys.stderr)
    if "弟弟" not in result.merchant:
        print(f"警告: merchant 期望含「弟弟」，实际 {result.merchant!r}", file=sys.stderr)
    if "墙纸" not in result.note:
        print(f"警告: note 期望含「墙纸」，实际 {result.note!r}", file=sys.stderr)

    print(f"\n{'=' * 60}")
    print("验收通过：已输出合法 ParsedTransaction")


if __name__ == "__main__":
    main()
