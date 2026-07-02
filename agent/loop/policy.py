"""Loop 硬限制常量 — 全项目统一的循环策略数值。

硬限制 vs 软限制：

- **硬限制**（本文件）：Harness 与 ``config["recursion_limit"]`` 强制执行，模型无法绕过
- **软限制**（``prompt.py``）：写入 system prompt，引导模型自觉停止；Harness 用 streak 兜底

与 ``graph/agent.invoke()`` 的区别：

- ``invoke()`` 使用 ``MAX_TOOL_ROUNDS * 2 + 1``（约 11 步），M4 基线路径
- ``invoke_v2()`` 使用下方 ``RECURSION_LIMIT``（15 步），M10 Loop 路径
"""

# 全局递归深度：硬限制， 本轮 invoke 内从 1 递增（非 LangGraph 全局递归深度）
RECURSION_LIMIT = 15

# 同一工具连续「无结果」多少次后强制中断（见 harness.is_no_tool_result）
SAME_TOOL_NO_RESULT_LIMIT = 3

# 触发软/硬兜底时的固定用户可见回复（与 system prompt 保持一致）
SAME_TOOL_GIVE_UP_REPLY = "我搞不定"
