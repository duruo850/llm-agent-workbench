"""Loop 软限制规则 — 拼接到 system prompt，引导模型自觉控制循环。

为什么需要软 + 硬两层：

1. **Prompt（本文件）**：让模型在 reasoning 阶段就意识到「别死磕同一工具」
2. **Harness（harness.py）**：模型若无视 prompt，``same_tool_streak`` 仍会强制中断

引用方：``agent/agent/promt/system_not_tools.py`` 在 ``system_prompt()`` 末尾拼接 ``LOOP_ENGINEERING_RULES``。
数值与 ``policy.py`` 保持同源，避免 prompt 写 3 次、代码写 5 次的不一致。
"""

from agent.loop.policy import SAME_TOOL_GIVE_UP_REPLY, SAME_TOOL_NO_RESULT_LIMIT

LOOP_ENGINEERING_RULES = f"""\
循环工程规则(必须遵守):
- 若**连续 {SAME_TOOL_NO_RESULT_LIMIT} 次**调用**同一工具**且均无有效结果, **停止再调工具**, 直接回复: "{SAME_TOOL_GIVE_UP_REPLY}"
- "无结果"指: 空返回, 仅错误信息, 对用户问题无实质帮助的 JSON
- 避免无意义重复调用同一工具; 换思路或直接向用户说明无法完成
"""
