"""M3 支付截图视觉识别 — 复用 M0 Ollama VISION 链。"""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from common.llm import LLMCapability, LLMProvider, get_openai_chat_llm
from server.model.request.parsed import LoadTransaction, ParsedTransaction

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


def _build_image_parse_chain():
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
    return prompt | llm | StrOutputParser()


def _validate_image_data_url(image_data_url: str) -> None:
    if not image_data_url.startswith("data:image/"):
        raise ValueError("image_data_url 必须是 data:image/...;base64,... 格式")


def format_vision_summary(tx: ParsedTransaction) -> str:
    return (
        f"从支付截图识别：金额 {tx.amount} 元，分类「{tx.category}」，"
        f"商户「{tx.merchant}」，备注「{tx.note}」"
    )


async def parse_receipt_image(image_data_url: str) -> str:
    """从 data URL 识别支付截图，返回供 Agent 消费的结构化摘要。"""
    _validate_image_data_url(image_data_url)
    chain = _build_image_parse_chain()
    raw_output = await chain.ainvoke({"image_url": image_data_url})
    tx = LoadTransaction(raw_output)
    return format_vision_summary(tx)
