# 里程碑索引 M0–M14

- **learning-plan** = 长期课表：[`docs/learning-plan.md`](../../docs/learning-plan.md)
- **Changes** = 可执行交付单：[`.harness/Changes/`](../Changes/)
- **定 plan 并实现** = [Skills/implement-plan/SKILL.md](../Skills/implement-plan/SKILL.md)

## 进度总览

| 里程碑 | 状态 | 交付物 | Changes |
|--------|------|--------|---------|
| **M0** | ✅ 完成 | LangChain 文本入账 + Ollama 视觉 | [M0_1-langchain-text](../Changes/M0_1-langchain-text.plan)、[M0_2-ollama-vision](../Changes/M0_2-ollama-vision.plan) |
| **M1** | ✅ 完成 | FastAPI + PostgreSQL CRUD | —（完成于 harness 前，无编号 plan） |
| **M2** | ✅ 完成 | Function Calling 记一笔 / 查账 | [M2_1-function-calling](../Changes/M2_1-function-calling.plan) |
| **M3** | ✅ 完成 | 聊天前端 | [M3_1-chat-frontend](../Changes/M3_1-chat-frontend.plan) |
| **M4** | ✅ 完成 | LangGraph Agent + 多账号鉴权 | [M4_1-langgraph-agent](../Changes/M4_1-langgraph-agent.plan)、[M4_2-accounts-auth](../Changes/M4_2-accounts-auth.plan) |
| **M5** | ✅ 完成 | 文件导入 | [M5_1-file-import](../Changes/M5_1-file-import.plan) |
| **M6** | ⬜ 待做 | MCP 功能研究；高德 MCP 接入（IP → 城市 / 天气） | — |
| **M7** | ⬜ 待做 | RAG 知识库 | — |
| **M8** | ⬜ 待做 | Embeddings 语义搜账 | — |
| **M9** | ⬜ 待做 | 月报工作流 | — |
| **M10** | ⬜ 待做 | Memory + HITL | — |
| **M11** | ⬜ 待做 | Eval + LangSmith | — |
| **M12** | ⬜ 待做 | Skills 模块 | — |
| **M13** | ⬜ 待做 | Fine-tuning | — |
| **M14** | ⬜ 待做 | 前端仪表盘 | — |

### 状态符号

| 符号 | 含义 |
|------|------|
| ✅ 完成 | 该里程碑所有 plan 均为 done，或已交付且无未完成 plan |
| 🔄 进行中 | 至少一个 plan 为 draft / in_progress |
| ⬜ 待做 | 尚未创建 plan 且未开始 |

## M0 要点

- 文本链：`examples/00_hello_chain.py` + `common/llm/`
- 视觉链：`examples/01_image_ollama_chain/`
- 解析结构：`ParsedTransaction`（[`server/model/request/parsed.py`](../../server/model/request/parsed.py)）

## M1 要点

- 服务端：[`server/`](../../server/)
- 三表：`categories`、`budgets`、`transactions`
- HTTP 集成测试：[`server/api/*_test.py`](../../server/api/)
- 规范：本 harness Rules + Skills

## M2 要点

- Agent 层：[`agent/agent.py`](../../agent/agent.py) + [`agent/skills/`](../../agent/skills/)
- CLI demo：[`examples/02_function_calling_agent.py`](../../examples/02_function_calling_agent.py)
- HTTP：`POST /agent/chat`
- 测试：[`server/api/agent_test.py`](../../server/api/agent_test.py)

## M4 要点

- Agent 层：[`agent/graph/`](../../agent/graph/)（LangGraph）；对照学习见 [`agent/agent/`](../../agent/agent/)（M2 for 循环）
- 跨轮记忆：`thread_id` 经 API / Web 透传
- 多账号：`POST /auth/login` + Bearer 鉴权；Agent skill 显式 `account_id` 参数
- 知识点：[`docs/knowledge/langgraph.md`](../../docs/knowledge/langgraph.md)
- CLI demo：[`examples/02_function_calling_agent.py`](../../examples/02_function_calling_agent.py)（`--repl` 复用 thread_id）
- HTTP：`POST /agent/chat`（request/response 含 `thread_id`）
- 测试：[`server/api/agent_test.py`](../../server/api/agent_test.py)、[`server/api/auth_test.py`](../../server/api/auth_test.py)

## M6 要点（规划）

- **MCP 功能研究**：Model Context Protocol 接入方式、与 Agent skill / LangGraph 集成路径
- **高德 MCP**：接入高德 MCP Server；通过客户端 IP 解析城市，并查询当地天气
- 交付方向：MCP 工具注册 + Agent 可调用（或独立 demo）；具体 plan 待 `M6_1-*.plan`

## M2+ 启动前

1. 读 [architecture.md](architecture.md) 了解 Agent 接入点
2. 用 [implement-plan](../Skills/implement-plan/SKILL.md) 创建 `M{n}_1-*.plan`
3. 按 plan 中的 `skills` 字段执行对应 Skill（如 [entity-service](../Skills/entity-service/SKILL.md)）
4. 验收通过后更新本表进度

## 新建交付单

命名：`M{n}_{seq}-{slug}.plan`（seq 在该 M{n} 下递增）。

流程见 [implement-plan](../Skills/implement-plan/SKILL.md)。完成后：

1. plan frontmatter `status: done`
2. 本表 Changes 列追加链接
3. 该 M{n} 全部 plan done 时，状态改为 ✅
