# AI 知识点索引

本目录是 [learning-plan.md](../learning-plan.md) 的**深度补充**：不讲课表与验收清单，而讲各技术的**本质**、核心流程，以及 BillMind 代码中的具体落点。

| 主题 | 里程碑 | 文档 | 代码入口 | 状态 |
|------|--------|------|----------|------|
| LangChain 基础（LCEL / Prompt / Chain） | M0 | [langchain-basics.md](langchain-basics.md) | `examples/00_hello_chain.py`, `common/llm/` | 待提取 |
| Function Calling | M2 | [function-calling.md](function-calling.md) | `agent/agent.py`, `agent/skills/` | done |
| LangGraph 状态图 Agent | M4 | [langgraph.md](langgraph.md) | `graph/graph.py`, `graph/agent.py` | done |
| RAG / LlamaIndex | M6 | [rag.md](rag.md) | `indexer/`（待建） | 待提取 |
| Embeddings 语义检索 | M7 | [embeddings.md](embeddings.md) | 待建 | 待提取 |
| Memory + Human-in-the-loop | M9 | [memory-hitl.md](memory-hitl.md) | 待建 | 待提取 |
| Eval + LangSmith | M10 | [eval-langsmith.md](eval-langsmith.md) | 待建 | 待提取 |
| 可插拔 Agent Skills | M11 | [agent-skills.md](agent-skills.md) | `agent/skills/`（待建） | 待提取 |
| Fine-tuning / LoRA | M12 | [fine-tuning.md](fine-tuning.md) | 待建 | 待提取 |

## 如何使用

1. 按 learning-plan 学到某个里程碑后，来本目录读对应「本质」文档。
2. 需要新增或更新知识点时，使用 harness Skill：[extract-ai-knowledge](../../.harness/Skills/extract-ai-knowledge/SKILL.md)。

## 相关链接

- 课表与实战任务：[docs/learning-plan.md](../learning-plan.md)
- 架构与数据流：[.harness/Wiki/architecture.md](../../.harness/Wiki/architecture.md)
- 里程碑进度：[.harness/Wiki/milestones.md](../../.harness/Wiki/milestones.md)
