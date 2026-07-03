"""BillMind 离线 Agent Eval(M11)

本包提供**不启动 FastAPI / 不走 HTTP** 的 Agent 质量评测：

- ``run_eval.py`` — 进程内初始化 LangGraph Agent,逐条跑用例并输出报告
- ``scorers.py`` — 纯函数打分（工具链 + 回复关键词 + 可选 LLM judge)
- ``scorers_test.py`` — 只测 scorers 逻辑，不调 LLM / DB
- ``test_cases.json`` — 用例集（用户消息 + 期望工具 + 关键词）

依赖:PostgreSQL(skills 读写账),``.env`` 中 ``DEEPSEEK_API_KEY``;**不需要** ``python server/main.py``。
"""
