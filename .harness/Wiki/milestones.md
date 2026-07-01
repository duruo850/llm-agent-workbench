# 里程碑索引 M0–M14

- **learning-plan** = 长期课表：`[docs/learning-plan.md](../../docs/learning-plan.md)`
- **Changes** = 可执行交付单：`[.harness/Changes/](../Changes/)`
- **定 plan 并实现** = [Skills/implement-plan/SKILL.md](../Skills/implement-plan/SKILL.md)

## 进度总览


| 里程碑     | 状态   | 交付物                              | Changes                                                                                                               |
| ------- | ---- | -------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **M0**  | ✅ 完成 | LangChain 文本入账 + Ollama 视觉       | [M0_1-langchain-text](../Changes/M0_1-langchain-text.plan)、[M0_2-ollama-vision](../Changes/M0_2-ollama-vision.plan)   |
| **M1**  | ✅ 完成 | FastAPI + PostgreSQL CRUD        | —（完成于 harness 前，无编号 plan）                                                                                             |
| **M2**  | ✅ 完成 | Function Calling 记一笔 / 查账        | [M2_1-function-calling](../Changes/M2_1-function-calling.plan)                                                        |
| **M3**  | ✅ 完成 | 聊天前端                             | [M3_1-chat-frontend](../Changes/M3_1-chat-frontend.plan)                                                              |
| **M4**  | ✅ 完成 | LangGraph Agent + 多账号鉴权          | [M4_1-langgraph-agent](../Changes/M4_1-langgraph-agent.plan)、[M4_2-accounts-auth](../Changes/M4_2-accounts-auth.plan) |
| **M5**  | ✅ 完成 | 文件导入                             | [M5_1-file-import](../Changes/M5_1-file-import.plan)                                                                  |
| **M6**  | ✅ 完成 | MCP 功能研究；高德 MCP 接入（IP → 城市 / 天气） | [M6_1-amap-mcp](../Changes/M6_1-amap-mcp.plan)                                                                        |
| **M7**  | ✅ 完成 | RAG 知识库（Milvus + Ollama）          | [M7_1-rag-knowledge](../Changes/M7_1-rag-knowledge.plan)                                                                        |
| **M8**  | ✅ 完成 | Embeddings 语义搜账                  | [M8_1-txn-semantic-search](../Changes/M8_1-txn-semantic-search.plan)                                                                                                                     |
| **M9**  | ⬜ 待做 | 月报工作流                            | —                                                                                                                     |
| **M10** | ⬜ 待做 | Memory + HITL                    | —                                                                                                                     |
| **M11** | ⬜ 待做 | Eval + LangSmith                 | —                                                                                                                     |
| **M12** | ⬜ 待做 | Skills 模块                        | —                                                                                                                     |
| **M13** | ⬜ 待做 | Fine-tuning                      | —                                                                                                                     |
| **M14** | ⬜ 待做 | 前端仪表盘                            | —                                                                                                                     |


### 状态符号


| 符号     | 含义                                 |
| ------ | ---------------------------------- |
| ✅ 完成   | 该里程碑所有 plan 均为 done，或已交付且无未完成 plan |
| 🔄 进行中 | 至少一个 plan 为 draft / in_progress    |
| ⬜ 待做   | 尚未创建 plan 且未开始                     |


## M0 要点

- 文本链：`examples/00_hello_chain.py` + `common/llm/`
- 视觉链：`examples/01_image_ollama_chain/`
- 解析结构：`ParsedTransaction`（`[server/model/request/parsed.py](../../server/model/request/parsed.py)`）

## M1 要点

- 服务端：`[server/](../../server/)`
- 三表：`categories`、`budgets`、`transactions`
- HTTP 集成测试：`[server/api/*_test.py](../../server/api/)`
- 规范：本 harness Rules + Skills

## M2 要点

- Agent 层：`[agent/agent.py](../../agent/agent.py)` + `[agent/skills/](../../agent/skills/)`
- CLI demo：`[examples/02_function_calling_agent.py](../../examples/02_function_calling_agent.py)`
- HTTP：`POST /agent/chat`
- 测试：`[server/api/agent_test.py](../../server/api/agent_test.py)`

## M4 要点

- Agent 层：`[agent/graph/](../../agent/graph/)`（LangGraph）；对照学习见 `[agent/agent/](../../agent/agent/)`（M2 for 循环）
- 跨轮记忆：`thread_id` 经 API / Web 透传
- 多账号：`POST /auth/login` + Bearer 鉴权；Agent skill 显式 `account_id` 参数
- 知识点：`[docs/knowledge/langgraph.md](../../docs/knowledge/langgraph.md)`
- CLI demo：`[examples/02_function_calling_agent.py](../../examples/02_function_calling_agent.py)`（`--repl` 复用 thread_id）
- HTTP：`POST /agent/chat`（request/response 含 `thread_id`）
- 测试：`[server/api/agent_test.py](../../server/api/agent_test.py)`、`[server/api/auth_test.py](../../server/api/auth_test.py)`

## M6 要点

- **MCP 功能研究**：Model Context Protocol 接入方式、与 Agent skill / LangGraph 集成路径
- **高德 MCP**：`[agent/mcp/gaode/](../../agent/mcp/gaode/)` 共用 MCP 客户端；Streamable HTTP 连接 `mcp.amap.com`
- **REST**：`GET /geo/me`（IP → 省/市/天气）；Web header 展示
- **Agent**：`init_async` 合并 `maps_ip_location` + `maps_weather`；system prompt 允许本地天气查询
- 知识点：`[docs/knowledge/mcp-amap.md](../../docs/knowledge/mcp-amap.md)`
- CLI demo：`[examples/03_amap_mcp_demo.py](../../examples/03_amap_mcp_demo.py)`
- 测试：`[server/api/geo_test.py](../../server/api/geo_test.py)`

## M7 要点

- **知识源**：[`agent/knowledge/finance/`](../../agent/knowledge/finance/) — 理财知识 10 篇 Markdown
- **RAG 层**：[`agent/rag/`](../../agent/rag/) — Ollama `nomic-embed-text` → Milvus `billmind_knowledge`
- **Agent**：`search_knowledge` skill（[`agent/skills/knowledge.py`](../../agent/skills/knowledge.py)）
- **REST**：`GET /knowledge/search?q=...&kb=...`
- **基础设施**：根目录 `docker-compose.yml`（`milvus` + `ollama`）
- 知识点：[`docs/knowledge/rag.md`](../../docs/knowledge/rag.md)
- Demo：[`examples/04_rag_knowledge_demo.py`](../../examples/04_rag_knowledge_demo.py)
- 测试：[`agent/rag/indexer_test.py`](../../agent/rag/indexer_test.py)、[`server/api/knowledge_test.py`](../../server/api/knowledge_test.py)

## M8 要点

- **向量层**：[`agent/rag/transaction.py`](../../agent/rag/transaction.py) — `TransactionRagService` → Milvus `billmind_transactions`
- **Agent**：`search_similar_transactions` skill（[`agent/skills/transactions_semantic.py`](../../agent/skills/transactions_semantic.py)）
- **REST**：`GET /transactions/search?q=...&top_k=...`
- **CLI 全量同步**：`python -m agent.rag.transaction --account-id <id>`
- **增量索引**：`TXN_SEARCH_INCREMENTAL`（默认开）；记账 / CSV 导入后 `transaction_rag.create*`
- 知识点：[`docs/knowledge/txn-semantic-search.md`](../../docs/knowledge/txn-semantic-search.md)
- Demo：[`examples/05_txn_semantic_demo.py`](../../examples/05_txn_semantic_demo.py)
- 测试：[`agent/rag/transaction_test.py`](../../agent/rag/transaction_test.py)、[`server/api/transactions_search_test.py`](../../server/api/transactions_search_test.py)

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

