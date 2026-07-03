# AI 知识点索引

本目录是 [learning-plan.md](../learning-plan.md) 的**深度补充**：不讲课表与验收清单，而讲各技术的**本质**、核心流程，以及 BillMind 代码中的具体落点。

文件名格式：**`M{n}-{slug}.md`**，便于与里程碑对应。

| 主题 | 里程碑 | 文档 | 代码入口 | 状态 |
|------|--------|------|----------|------|
| LangChain 基础（LCEL / Prompt / Chain） | M0 | [M0-langchain-basics.md](M0-langchain-basics.md) | `examples/00_hello_chain.py`, `common/llm/` | 待提取 |
| Function Calling | M2 | [M2-function-calling.md](M2-function-calling.md) | `agent/agent.py`, `agent/skills/` | done |
| LangGraph 状态图 Agent | M4 | [M4-langgraph.md](M4-langgraph.md) | `graph/graph.py`, `graph/agent.py` | done |
| MCP + 高德（IP / 天气） | M6 | [M6-mcp-amap.md](M6-mcp-amap.md) | `agent/mcp/gaode/`, `server/api/geo.py` | done |
| RAG / Milvus + Ollama Embedding | M7 | [M7-rag.md](M7-rag.md) | `agent/storage/rag/`, `agent/knowledge/`, `GET /knowledge/search` | done |
| Embeddings 语义检索 | M8 | [M8-txn-semantic-search.md](M8-txn-semantic-search.md) | `agent/storage/rag/transaction.py`, `GET /transactions/search` | done |
| Memory OS（分层存储 + 流水线） | M9 | [M9-memory-os.md](M9-memory-os.md) | `agent/storage/`, `AsyncPostgresSaver` | done |
| Loop Engineering（Harness + 步级落库） | M10 | [M10-loop-engineering.md](M10-loop-engineering.md) | `agent/loop/`, `invoke_v2` | done |
| Eval + LangSmith | M11 | [M11-eval-langsmith.md](M11-eval-langsmith.md) | `test/eval/`, `invoke` + `LANGSMITH_*` | done |
| Memory + Human-in-the-loop | M12 | [M12-memory-hitl.md](M12-memory-hitl.md) | 待建 | 待提取 |
| Fine-tuning / LoRA | M12 | [M12-fine-tuning.md](M12-fine-tuning.md) | 待建 | 待提取 |
| 可插拔 Agent Skills | M14 | [M14-agent-skills.md](M14-agent-skills.md) | `agent/skills/`（待建） | 待提取 |
| Agent 延迟与成本优化 | — | [agent-optimization.md](agent-optimization.md) | `agent/agent/promt/system.py`, `common/llm/setting.py` | done |

## 如何使用

1. 按 learning-plan 学到某个里程碑后，来本目录读对应「本质」文档。
2. 需要新增或更新知识点时，使用 harness Skill：[extract-ai-knowledge](../../.harness/Skills/extract-ai-knowledge/SKILL.md)。

## 相关链接

- 课表与实战任务：[docs/learning-plan.md](../learning-plan.md)
- 架构与数据流：[.harness/Wiki/architecture.md](../../.harness/Wiki/architecture.md)
- 里程碑进度：[.harness/Wiki/milestones.md](../../.harness/Wiki/milestones.md)
