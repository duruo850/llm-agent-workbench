"""工具 prompt 编排元数据 — 供 ``system_not_tools`` / ``system`` 自动生成规则。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agent.common.skill_category import SkillCategoryId

SessionFactory = async_sessionmaker[AsyncSession]

OUT_OF_SCOPE_REPLY = "抱歉, BillMind 仅支持账单记账与查询相关业务."


@dataclass(frozen=True)
class ToolPromptPolicy:
    """单个 @tool 在 system prompt 中的编排说明（与 docstring 互补）。"""

    scope: str  # 业务范围
    skill_category: SkillCategoryId  # 分类ID
    time_scope: Literal["day", "month", "none"] = "none"  # 时间范围
    user_triggers: tuple[str, ...] = ()  # 用户触发词
    month_triggers: tuple[str, ...] = ("本月", "这个月")  # 月份触发词
    time_param: str = ""  # 时间参数
    forbid_tools: tuple[str, ...] = ()  # 禁止使用的工具
    example_queries: tuple[str, ...] = ()  # 示例查询
    example_note: str = ""  # 示例说明


def account_id_from_config(config: RunnableConfig) -> int:
    """从 RunnableConfig.configurable 读取当前登录账号 ID。"""
    account_id = config.get("configurable", {}).get("account_id")
    if account_id is None:
        raise RuntimeError("RunnableConfig.configurable 缺少 account_id")
    return int(account_id)
