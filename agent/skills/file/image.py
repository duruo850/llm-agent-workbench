"""图片文件 skill — 多模态识别支付截图。"""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent.promt.image import IMAGE_SYSTEM_PROMPT
from agent.agent.promt.policy import tool_policy
from common.format import format_tool_result
from common.llm import LLMCapability, LLMProvider, get_openai_chat_llm
from server.model.request.parsed import LoadTransaction


async def recognize_image_file(image_data_url: str) -> str:
    """多模态链：从 data URL 提取记账摘要文本。"""
    if not image_data_url.startswith("data:image/"):
        raise ValueError("image_data_url 必须是 data:image/...;base64,... 格式")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", IMAGE_SYSTEM_PROMPT),
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
    chain = prompt | llm | StrOutputParser()
    raw_output = await chain.ainvoke({"image_url": image_data_url})
    tx = LoadTransaction(raw_output)
    return (
        f"从支付截图识别：金额 {tx.amount} 元，分类「{tx.category}」，"
        f"商户「{tx.merchant}」，备注「{tx.note}」"
    )


@tool_policy(
    scope="图片文件识别",
    user_triggers=("截图", "图片", "支付截图", "转账截图"),
    example_queries=("识别这张支付截图",),
    example_note="用户上传图片时使用 parse_image_file（多模态），不要用于 CSV",
)
async def parse_image_file(
    db: AsyncSession,
    image_data_url: str,
    *,
    config: RunnableConfig,
) -> str:
    """从支付/转账截图 data URL 识别记账信息（多模态视觉模型）。

    Args:
        image_data_url: data:image/...;base64,... 格式。
    """
    del db, config
    summary = await recognize_image_file(image_data_url)
    return format_tool_result({"message": summary, "summary": summary})
