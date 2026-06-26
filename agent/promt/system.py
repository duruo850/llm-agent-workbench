"""系统 prompt 生成器。"""

from __future__ import annotations

from datetime import datetime
from langchain_core.tools import BaseTool
from agent.promt.policy import OUT_OF_SCOPE_REPLY
from agent.skills import SKILL_POLICYS


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

    day_tools = [t for t in tools if (p := SKILL_POLICYS.get(t.name)) and p.time_scope == "day"]
    month_tools = [t for t in tools if (p := SKILL_POLICYS.get(t.name)) and p.time_scope == "month"]

    for registered in day_tools:
        policy = SKILL_POLICYS.get(registered.name)
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
        month_triggers = SKILL_POLICYS[month_tools[0].name].month_triggers if month_tools else ()
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
        policy = SKILL_POLICYS.get(registered.name)
        if policy and policy.scope and policy.scope not in scopes:
            scopes.append(policy.scope)

    scope_text = "、".join(scopes) if scopes else "（无）"
    return f"""\
业务范围（必须遵守）：
- **仅处理**：{scope_text}
- 对投资、报税、闲聊、天气、通用问答等与账单无关的请求：**不要调用任何工具**，直接回复：
  「{OUT_OF_SCOPE_REPLY}」"""


def system_prompt(tools: list[BaseTool]) -> str:
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