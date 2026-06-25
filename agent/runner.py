"""M2 Agent Runner — bind_tools + tool-call 循环。

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

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from agent.function_calling import execute_tool_calls
from agent.tools.db_tools import get_db_tools
from common.llm import LLMCapability, LLMProvider, get_openai_chat_llm
from utils.map_by_name import map_by_name

MAX_TOOL_ROUNDS = 5

_SYSTEM_PROMPT = """\
你是 BillMind 个人记账助手。用户会用自然语言记一笔账或查询消费情况。

你可以使用工具完成操作：
- add_transaction：记一笔
- query_transactions：查询某月交易列表
- get_monthly_summary：查询某月分类汇总与总支出

规则：
- 记一笔时从用户话里提取 amount、category、merchant、note
- 查账时先判断用户要的月份（未说明则用当前月份，格式 YYYY-MM）
- 工具返回 JSON 后，用简洁中文回复用户，说明结果
"""


async def invoke_agent(message: str, *, db: AsyncSession, debug: bool = False) -> str:
    """处理单条用户消息，返回 Agent 自然语言回复。

    Args:
        message: 用户自然语言输入。
        db: 异步数据库 session，由调用方注入（Server ``Depends(get_db)`` 或 CLI session）。
    """
    tools = get_db_tools(db)
    tools_map = map_by_name(tools)

    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        temperature=0,
    ).bind_tools(tools)

    messages: list = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=message),
    ]

    if debug:
        print(f"\n▸ 用户输入: {message}")

    for round_idx in range(MAX_TOOL_ROUNDS):
        response = await llm.ainvoke(messages)
        if debug:
            print(f"\n▸ LLM 第 {round_idx + 1} 轮回复")
            if response.tool_calls:
                print(f"  tool_calls: {response.tool_calls}")
            else:
                print(f"  content: {response.content}")

        messages.append(response)

        if not response.tool_calls:
            content = response.content
            return content if isinstance(content, str) else str(content)

        tool_messages = await execute_tool_calls(response, tools_map, debug=debug)
        messages.extend(tool_messages)

    last = messages[-1]
    if isinstance(last, AIMessage):
        content = last.content
        return content if isinstance(content, str) else str(content)
    return "已达到最大工具调用轮数，请简化请求后重试。"
