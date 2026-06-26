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

import logging
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from sqlalchemy.ext.asyncio import AsyncSession

from agent.function_calling import execute_tool_calls
from agent.tools.db_tools import get_db_tools, get_tool_policy
from agent.tools.policy import OUT_OF_SCOPE_REPLY
from common.llm import LLMCapability, LLMProvider, get_openai_chat_llm
from utils.map_by_name import map_by_name

MAX_TOOL_ROUNDS = 5

logger = logging.getLogger("billmind.agent")


def _tool_summary(tool: BaseTool) -> str:
    """从 @tool docstring 提取首段摘要，供 system prompt 列举。"""
    desc = (tool.description or "").strip()
    if not desc:
        return ""
    summary = desc.split("\n\n")[0].replace("\n", " ").strip()
    for marker in ("Args:", "Parameters:"):
        if marker in summary:
            summary = summary.split(marker)[0].strip()
    return summary


def _format_tools_section(tools: list[BaseTool]) -> str:
    """遍历 bind_tools 同源列表，自动生成工具说明（与 db_tools 保持同步）。"""
    lines: list[str] = []
    for tool in tools:
        summary = _tool_summary(tool)
        lines.append(f"- {tool.name}：{summary}" if summary else f"- {tool.name}")
    return "\n".join(lines)


def _format_time_range_rules(tools: list[BaseTool], today_date: str, month: str) -> str:
    """从各 tool 的 ToolPromptPolicy 生成时间范围编排规则。"""
    lines: list[str] = []

    day_tools = [t for t in tools if (p := get_tool_policy(t)) and p.time_scope == "day"]
    month_tools = [t for t in tools if (p := get_tool_policy(t)) and p.time_scope == "month"]

    for registered in day_tools:
        policy = get_tool_policy(registered)
        if policy is None:
            continue
        triggers = "」「".join(policy.user_triggers)
        param = f"{policy.time_param}={today_date}" if policy.time_param == "date" else ""
        forbid = ""
        if policy.forbid_tools:
            forbid = f"；禁止调用 {'、'.join(policy.forbid_tools)}"
        lines.append(
            f"- 用户说「{triggers}」→ 必须调用 {registered.name}，{param}{forbid}"
        )
        for example in policy.example_queries:
            note = policy.example_note.format(today_date=today_date, month=month)
            lines.append(f"- 「{example}」= {note}")

    if month_tools:
        month_triggers = get_tool_policy(month_tools[0]).month_triggers if month_tools else ()
        triggers = "」「".join(month_triggers)
        names = " 或 ".join(t.name for t in month_tools)
        lines.append(
            f"- 用户说「{triggers}」或未指明是「今天」→ 调用 {names}，month={month}"
        )

    return "\n".join(lines) if lines else "- （当前无时间范围相关工具）"


def _format_business_scope(tools: list[BaseTool]) -> str:
    """从各 tool 的 ToolPromptPolicy.scope 汇总业务范围。"""
    scopes: list[str] = []
    for registered in tools:
        policy = get_tool_policy(registered)
        if policy and policy.scope and policy.scope not in scopes:
            scopes.append(policy.scope)

    scope_text = "、".join(scopes) if scopes else "（无）"
    return f"""\
业务范围（必须遵守）：
- **仅处理**：{scope_text}
- 对投资、报税、闲聊、天气、通用问答等与账单无关的请求：**不要调用任何工具**，直接回复：
  「{OUT_OF_SCOPE_REPLY}」"""


def _system_prompt(tools: list[BaseTool]) -> str:
    today = datetime.now().replace(microsecond=0)
    month = today.strftime("%Y-%m")
    today_date = today.strftime("%Y-%m-%d")
    # 自动生成工具说明
    tools_section = _format_tools_section(tools)
    # 自动生成时间范围规则
    time_range_section = _format_time_range_rules(tools, today_date, month)
    # 自动生成业务范围
    business_scope_section = _format_business_scope(tools)
    return f"""\
你是 BillMind 个人记账助手。用户会用自然语言记一笔账或查询消费情况。

今天是 {today_date}，当前月份是 {month}。

你可以使用工具完成操作（与 bind_tools 注册列表一致，新增工具会自动出现在此）：
{tools_section}

时间范围规则（必须遵守）：
{time_range_section}

业务范围（必须遵守）：
{business_scope_section}

规则：
- 记一笔时从用户话里提取 amount、category、merchant、note
- 若消息中含「从支付截图识别：」段落，将其视为已解析的记账信息，可据此记一笔或向用户确认
- 工具返回 JSON 后，用简洁中文回复用户，说明结果
"""


async def invoke_agent(message: str, *, db: AsyncSession, debug: bool = False) -> str:
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

    # 本地可执行工具；tools_map 供 execute_tool_calls 按 name 分发
    tools = get_db_tools(db)
    tools_map = map_by_name(tools)

    # bind_tools：向 LLM 注入机器可读的工具定义，使其能发出 tool_calls
    llm = get_openai_chat_llm(
        provider=LLMProvider.DEEPSEEK,
        capability=LLMCapability.TEXT,
        temperature=0,
    ).bind_tools(tools)

    # system_prompt：传入同一 tools 列表，自动列举工具 + 业务编排规则
    messages: list = [
        SystemMessage(content=_system_prompt(tools)),
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

        tool_messages = await execute_tool_calls(response, tools_map, debug=debug)
        messages.extend(tool_messages)
    else:
        last = messages[-1]
        if isinstance(last, AIMessage):
            content = last.content
            reply = content if isinstance(content, str) else str(content)

    logger.info("output: %s", reply)
    return reply
