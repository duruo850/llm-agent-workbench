"""system_prompt 单元测试 — 默认路径 ``system_not_tools``，``system`` 为按 tools 过滤变体。"""

from __future__ import annotations

from langchain_core.tools import StructuredTool

from agent.agent.promt.policy import OUT_OF_SCOPE_REPLY, ToolPromptPolicy
from agent.agent.promt.system import system_prompt as system_prompt_for_tools
from agent.agent.promt.system_not_tools import system_prompt
from agent.loop.prompt import LOOP_ENGINEERING_RULES
from agent.skills import SKILL_POLICYS


def _fake_tool(name: str, description: str) -> StructuredTool:
    def _noop(**kwargs: object) -> str:
        del kwargs
        return ""

    return StructuredTool.from_function(
        func=_noop,
        name=name,
        description=description,
    )


def _representative_tools() -> list[StructuredTool]:
    """模拟 bind_tools 列表：长 docstring 不应再进入 system prompt。"""
    long_desc = (
        "查询指定日期的消费汇总，返回总支出、分类 breakdown 与笔数。"
        " Args: date — YYYY-MM-DD。"
        " Parameters: account_id 从 config 注入。"
    )
    return [
        _fake_tool("get_daily_summary", long_desc),
        _fake_tool(
            "find_closest_transaction",
            "在指定日期查找最接近目标金额的一笔交易。Args: date, target_amount。",
        ),
        _fake_tool(
            "search_similar_transactions",
            "按语义搜索历史消费记录，适用于模糊回忆场景。",
        ),
        _fake_tool(
            "get_monthly_summary",
            "查询指定月份的消费汇总。Args: month — YYYY-MM。",
        ),
        _fake_tool("import_csv_file", "从 CSV 文本批量导入交易。"),
        _fake_tool("parse_image_file", "从支付截图 data URL 识别记账信息。"),
    ]


def _register_test_policies() -> None:
    policies = {
        "get_daily_summary": ToolPromptPolicy(
            scope="账单查询",
            time_scope="day",
            user_triggers=("今天", "今日"),
            time_param="date",
            forbid_tools=("get_monthly_summary",),
            example_queries=("今天花了多少",),
            example_note="今天总支出，date={today_date}",
        ),
        "get_monthly_summary": ToolPromptPolicy(
            scope="账单查询",
            time_scope="month",
        ),
        "parse_image_file": ToolPromptPolicy(scope="图片文件识别"),
        "import_csv_file": ToolPromptPolicy(scope="CSV 导入"),
    }
    SKILL_POLICYS.update(policies)


def _legacy_tools_section(tools: list[StructuredTool]) -> str:
    """改前 _format_tools_section 的等价输出，用于对比精简幅度。"""
    lines: list[str] = []
    for tool in tools:
        desc = (tool.description or "").strip()
        summary = desc.split("\n\n")[0].replace("\n", " ").strip()
        lines.append(f"- {tool.name}：{summary}" if summary else f"- {tool.name}")
    return "\n".join(lines)


def _assert_orchestration_rules(prompt: str) -> None:
    assert "bind_tools schema" in prompt
    assert "时间范围规则" not in prompt
    assert "单日查询意图" not in prompt
    assert OUT_OF_SCOPE_REPLY in prompt
    assert "import_csv_file" in prompt
    assert "parse_image_file" in prompt
    assert "不要展示推理过程" in prompt
    assert "recognize_image_file" not in prompt
    assert LOOP_ENGINEERING_RULES.strip() in prompt


def test_system_not_tools_prompt_is_slim_without_tool_list() -> None:
    tools = _representative_tools()
    prompt = system_prompt()

    legacy_block = _legacy_tools_section(tools)
    assert legacy_block not in prompt
    assert len(prompt) < len(legacy_block) + 1200
    assert len(prompt) < 2500
    assert len(prompt) // 3 < 800


def test_system_not_tools_prompt_retains_orchestration_rules() -> None:
    _assert_orchestration_rules(system_prompt())


def test_system_not_tools_is_slimmer_than_system_prompt() -> None:
    """``system_not_tools`` 应比 ``system.system_prompt(tools)`` 更短（无工具枚举等）。"""
    tools = _representative_tools()
    _register_test_policies()
    slim = system_prompt()
    full = system_prompt_for_tools(tools)

    assert len(slim) < len(full)
    assert "你可以使用工具完成操作" not in slim
    assert "单日查询意图" not in slim
