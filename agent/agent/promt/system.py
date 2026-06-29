"""系统 prompt 生成器。"""

from __future__ import annotations

from datetime import datetime
from langchain_core.tools import BaseTool
from agent.agent.promt.policy import OUT_OF_SCOPE_REPLY
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


def _format_intent_rules(tools: list[BaseTool], today_date: str) -> str:
    """单日查询意图分流 — 汇总 vs 最接近某金额。"""
    tool_names = {t.name for t in tools}
    lines: list[str] = []
    if "get_daily_summary" in tool_names:
        lines.append(
            f"- 「今天/今日花了多少」、总支出、分类汇总 → get_daily_summary，date={today_date}"
        )
    if "find_closest_transaction" in tool_names:
        lines.append(
            f"- 「最接近 X 元/块的是哪一笔」「哪笔离 X 最近」→ find_closest_transaction，"
            f"date={today_date}，target_amount=X；不要用 get_daily_summary 或 query_transactions"
        )
    return "\n".join(lines) if lines else "- （当前无单日意图分流规则）"


def _format_response_rules() -> str:
    return """\
- 用户明确要求「只要…」「只返回…」「不需要总数/全部/其他」时，严格按要求的粒度回复
- find_closest_transaction 只返回一笔时：只描述该笔（金额、分类、商户或备注），不要列举当天其他交易、不要报总笔数
- 工具已精确返回用户所需数据时，不要自行补充列表、表格或对比信息"""


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
    intent_section = _format_intent_rules(tools, today_date)
    response_section = _format_response_rules()
    # 自动生成业务范围
    business_scope_section = _format_business_scope(tools)
    return f"""\
你是 BillMind 个人记账助手。用户会用自然语言记一笔账或查询消费情况。

今天是 {today_date}，当前月份是 {month}。

你可以使用工具完成操作（与 bind_tools 注册列表一致，新增工具会自动出现在此）：
{tools_section}

时间范围规则（必须遵守）：
{time_range_section}

单日查询意图（必须遵守）：
{intent_section}

回复格式（必须遵守）：
{response_section}

业务范围（必须遵守）：
{business_scope_section}

规则：
- 记一笔时从用户话里提取 amount、category、merchant、note
- 若消息中含「从支付截图识别：」段落，将其视为已解析的记账信息，可据此记一笔或向用户确认
- 若消息中含「用户上传了 CSV 文件」及 csv_text 内容，按用户指令调用 import_csv_file（不要用图片 skill 处理 CSV）
- 若消息中含「用户上传了图片」及 image_data_url 内容，按用户意图调用 recognize_image_file（多模态）
- 工具返回 JSON 后，用简洁中文向用户说明处理结果；遵守上方「回复格式」
"""