"""M2 数据库工具 — 将 M1 REST API 封装为 LangChain @tool。

Function Calling 与 AI 的关系（本模块在整条链路中的位置）：

1. **用户自然语言** → LLM（`agent/runner.py`）理解意图。
2. **LLM 不直接写数据库**，而是根据工具 docstring 与 JSON Schema，在回复中生成
   ``tool_calls``（函数名 + 参数），即「我想调用 add_transaction(amount=38, ...)」。
3. **Runner 执行工具** — 本文件中的 ``@tool`` 函数被同步调用，内部用 httpx 请求
   ``POST/GET`` M1 API，把结构化操作落到 PostgreSQL。
4. **工具返回 JSON 字符串** → 作为 ``ToolMessage`` 回传给 LLM，LLM 再组织自然语言回复。

因此：``db_tools`` 是 AI「手脚」与业务 API「身体」之间的适配层；LLM 负责理解与决策，
工具负责确定性 I/O。

``_TOOL_POLICIES`` 与 docstring 一并维护：runner 自动生成功能说明、时间范围与业务范围。
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import BaseTool, tool
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from agent.tools.policy import ToolPromptPolicy
from server.service import transaction_service

_TOOL_POLICIES: dict[str, ToolPromptPolicy] = {
    "add_transaction": ToolPromptPolicy(scope="记一笔"),
    "query_transactions": ToolPromptPolicy(
        scope="查交易",
        time_scope="month",
        time_param="month",
    ),
    "get_daily_summary": ToolPromptPolicy(
        scope="查日汇总",
        time_scope="day",
        user_triggers=("今天", "今日", "当天"),
        time_param="date",
        forbid_tools=("get_monthly_summary",),
        example_queries=("我今天用了多少钱",),
        example_note="查今天（{today_date}），不是查本月",
    ),
    "get_monthly_summary": ToolPromptPolicy(
        scope="查月汇总",
        time_scope="month",
        time_param="month",
    ),
}


def get_tool_policy(tool: BaseTool) -> ToolPromptPolicy | None:
    return _TOOL_POLICIES.get(tool.name)


def _format_result(data: Any) -> str:
    if hasattr(data, "model_dump"):
        payload = data.model_dump(mode="json")
    elif isinstance(data, list):
        payload = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in data
        ]
    else:
        payload = data
    return json.dumps(payload, ensure_ascii=False, default=str)


def _format_db_error(exc: Exception) -> str:
    return json.dumps({"error": True, "detail": str(exc)}, ensure_ascii=False)


def get_db_tools(db: AsyncSession) -> list[BaseTool]:
    """根据注入的 db session 构建 LangChain 工具列表。"""

    @tool
    async def add_transaction(
        amount: float, category: str, merchant: str = "", note: str = ""
    ) -> str:
        """记一笔支出或收入。

        Args:
            amount: 金额，正数。
            category: 分类名，如「餐饮」「交通」「工资」。
            merchant: 商户或来源，如 Starbucks、地铁；未知可传空字符串。
            note: 补充说明，没有可传空字符串。
        """
        try:
            result = await transaction_service.create_transaction_from_agent(
                db,
                amount=amount,
                category=category,
                merchant=merchant,
                note=note,
            )
            return _format_result(result)
        except (IntegrityError, SQLAlchemyError) as exc:
            return _format_db_error(exc)

    @tool
    async def query_transactions(month: str, category: str | None = None) -> str:
        """查询指定月份的交易记录，可选按分类过滤。仅用于「某月」明细，不要用于「今天/今日」。

        Args:
            month: 月份，格式 YYYY-MM，如 2025-06。
            category: 可选分类名；传入时仅返回该分类下的记录。
        """
        try:
            rows = await transaction_service.list_transactions(db, month=month, category=category)
            return _format_result(rows)
        except SQLAlchemyError as exc:
            return _format_db_error(exc)

    @tool
    async def get_daily_summary(date: str) -> str:
        """获取指定日期的分类汇总、总支出与笔数，用于回答「今天/今日花了多少」。

        Args:
            date: 日期，格式 YYYY-MM-DD，如 2026-06-26。
        """
        try:
            summary = await transaction_service.get_daily_summary(db, date=date)
            return _format_result(summary)
        except SQLAlchemyError as exc:
            return _format_db_error(exc)

    @tool
    async def get_monthly_summary(month: str) -> str:
        """获取指定月份的分类汇总、总支出与笔数，用于回答「本月/这个月花了多少」。不要用于「今天/今日」。

        Args:
            month: 月份，格式 YYYY-MM，如 2025-06。
        """
        try:
            summary = await transaction_service.get_monthly_summary(db, month=month)
            return _format_result(summary)
        except SQLAlchemyError as exc:
            return _format_db_error(exc)

    return [add_transaction, query_transactions, get_daily_summary, get_monthly_summary]
