"""BillMind Agent — 初始化、对话、视觉识别与 Function Calling 执行。
M2 Agent Runner — bind_tools + tool-call 循环。

Function Calling 执行流程（与 AI 的协作方式）：

::

    用户: "刚才 Starbucks 花了 38，算餐饮"
      │
      ▼
    HumanMessage ──► LLM.bind_tools(tools).invoke(messages)
      │                    │
      │                    ▼
      │              AIMessage（可能含 tool_calls，而非最终文本）
      │                    │
      │         tool_calls 非空？──否──► 返回 content 给用户
      │                    │
      │                   是
      │                    ▼
      │         function_calling() → ToolMessage
      │                    │
      └────────────────────┘（追加到 messages，再次 invoke，最多 MAX_TOOL_ROUNDS 轮）

要点：
- **bind_tools**：把 ``db_tools`` 的 name / description / args schema 注入模型上下文。
- **tool_calls**：结构化调用意图，由 ``agent/function_calling.py`` 本地执行。
- **ToolMessage**：工具结果喂回模型，生成用户可读的自然语言总结。
- M4 LangGraph 将把此循环拆成显式节点；M2 用简易 for 循环即可。
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession

from agent.agent.promt.image import IMAGE_SYSTEM_PROMPT
from agent.agent.promt.system import system_prompt
from agent.agent.skills import SKILL_TOOLS, SKILL_TOOLS_MAP, discover_skill_modules
from common.llm import LLMCapability, LLMProvider, get_openai_chat_llm
from server.db.session import Database
from server.model.request.parsed import LoadTransaction

MAX_TOOL_ROUNDS = 5

logger = logging.getLogger("billmind.agent")


class Agent:
    """Agent 入口 — init / invoke / parse_image / function_calling"""

    @classmethod
    def init(cls) -> None:
        """在 ``Database.init`` 之后调用，加载 skill 工具与 prompt 策略。"""
        discover_skill_modules(Database.get().async_session_factory)
        logger.info("agent skills loaded: %s", ", ".join(SKILL_TOOLS))

    @classmethod
    async def invoke(
        cls,
        message: str,
        *,
        db: AsyncSession,
        debug: bool = False,
    ) -> str:
        """处理单条用户消息，返回 Agent 自然语言回复。

    ``bind_tools`` 与 ``_system_prompt`` 分工：

    - **bind_tools**：把本地 ``db_tools`` 注册进 LLM 请求（name / 参数 schema / docstring）。
      模型据此产出 ``tool_calls``；Runner 用 ``tools_map`` 在本地真正执行（查库、记账）。
      → 给 Runner **接上可执行的能力**。
    - **_system_prompt(tools)**：传入与 ``bind_tools`` 相同的工具列表，自动遍历生成工具说明；
      并补充使用策略（何时调哪个、越界拒答、当前日期等）。
      → 告诉 AI **如何正确运用**已注册的能力。

    Args:
        message: 用户自然语言输入。
        db: 异步数据库 session，由调用方注入（Server ``Depends(get_db)`` 或 CLI session）。
    """
        logger.info("input: %s", message)

        if not SKILL_TOOLS:
            raise RuntimeError("Agent 未初始化，请先调用 Agent.init()")

        tools = list(SKILL_TOOLS.values())

        llm = get_openai_chat_llm(
            provider=LLMProvider.DEEPSEEK,
            capability=LLMCapability.TEXT,
            temperature=0,
        ).bind_tools(tools)

        messages: list = [
            SystemMessage(content=system_prompt(tools)),
            HumanMessage(content=message),
        ]

        reply = "已达到最大工具调用轮数，请简化请求后重试。"

        for round_idx in range(MAX_TOOL_ROUNDS):
            response = await llm.ainvoke(messages)
            round_no = round_idx + 1
            if response.tool_calls:
                logger.info("llm round %d tool_calls: %s", round_no, response.tool_calls)
                if debug:
                    print(f"\n▸ LLM 第 {round_no} 轮 tool_calls: {response.tool_calls}")
            else:
                logger.info("llm round %d content: %s", round_no, response.content)
                if debug:
                    print(f"\n▸ LLM 第 {round_no} 轮 content: {response.content}")

            messages.append(response)

            if not response.tool_calls:
                content = response.content
                reply = content if isinstance(content, str) else str(content)
                break

            tool_messages = await cls.function_calling(
                response, SKILL_TOOLS_MAP, debug=debug
            )
            messages.extend(tool_messages)
        else:
            last = messages[-1]
            if isinstance(last, AIMessage):
                content = last.content
                reply = content if isinstance(content, str) else str(content)

        logger.info("output: %s", reply)
        return reply

    @classmethod
    async def parse_image(cls, image_data_url: str) -> str:
        """从 data URL 识别支付截图，返回供 Agent 消费的结构化摘要。"""
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

    @classmethod
    async def function_calling(
        cls,
        ai_message: AIMessage,
        tools_map: dict[str, BaseTool],
        *,
        debug: bool = False,
    ) -> list[ToolMessage]:
        """
        ai的function calling执行功能，调用本地工具，返回ToolMessage列表。
        执行模型输出的 tool_calls，返回 ToolMessage 列表。"""
        tool_messages: list[ToolMessage] = []
        
        # 遍历ai的tool_calls，调用本地工具，返回ToolMessage列表。
        for tool_call in ai_message.tool_calls:
            name = tool_call["name"]
            args: dict[str, Any] = tool_call["args"]
            tool_call_id = tool_call["id"]
            logger.info("tool invoke: %s(%s)", name, args)
            if debug:
                print(f"  ▸ 工具调用: {name}({args})")
            tool = tools_map.get(name)
            
            # 如果工具不存在，返回错误信息。
            if tool is None:
                content = f'{{"error": true, "detail": "未知工具: {name}"}}'
            else:
                # 如果工具存在，调用工具，返回结果。
                content = await tool.ainvoke(args)
            preview = content[:200] + ("..." if len(content) > 200 else "")
            logger.info("tool result: %s", preview)
            if debug:
                print(f"    返回: {preview}")
            tool_messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
        return tool_messages
