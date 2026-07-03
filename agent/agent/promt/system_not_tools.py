"""精简 system prompt — 不依赖 bind_tools 的 ``tools`` 列表。

DeepSeek / OpenAI Chat Completions 请求体里，**工具定义**与**对话**是两条通道：

- ``tools``（``bind_tools``）：JSON Schema + docstring，模型据此选型并产出 ``tool_calls``
- ``messages``（本模块）：``SystemMessage`` 正文，只放 schema 难以表达的规则（日期、拒答、附件协议等）

工具选型（含时间范围）交给 ``bind_tools`` + LLM；``_format_response_rules`` 复用 ``system.py``。
完整版（含工具枚举 / 时间编排）见 ``system.system_prompt(tools)``。

详见 ``docs/knowledge/agent-optimization.md`` §Tools 与 messages。
"""

from __future__ import annotations

from datetime import datetime

from agent.agent.promt.policy import OUT_OF_SCOPE_REPLY
from agent.agent.promt.system import _format_response_rules
from agent.loop.prompt import LOOP_ENGINEERING_RULES


def system_prompt() -> str:
    """生成 SystemMessage 正文；工具 schema 由 ``bind_tools`` 单独注入 API ``tools`` 参数。"""
    today = datetime.now().replace(microsecond=0)
    month = today.strftime("%Y-%m")
    today_date = today.strftime("%Y-%m-%d")
    return f"""\
你是 BillMind 个人记账助手。今天 {today_date}，本月 {month}。
与记账/查询无关的请求不调用工具，直接回复「{OUT_OF_SCOPE_REPLY}」

记账与查询请调用工具；工具定义见 bind_tools schema，勿在此重复列举。

回复格式（必须遵守）：
{_format_response_rules()}

附件与消息块：
- 记一笔时从用户话里提取 amount、category、merchant、note
- 若消息中含「从支付截图识别：」段落，将其视为已解析的记账信息，可据此记一笔或向用户确认
- 若消息中含「用户上传了 CSV 文件」及 csv_text 内容，按用户指令调用 import_csv_file（不要用图片 skill 处理 CSV）
- 若消息中含「用户上传了图片」及 image_data_url 内容，按用户意图调用 parse_image_file（多模态）
- 工具返回 JSON 后，用简洁中文向用户说明处理结果

{LOOP_ENGINEERING_RULES}"""
