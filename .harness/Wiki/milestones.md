# 里程碑索引 M0–M13

- **learning-plan** = 长期课表：[`docs/learning-plan.md`](../../docs/learning-plan.md)
- **Changes** = 可执行交付单：[`.harness/Changes/`](../Changes/)

## 进度总览

| 里程碑 | 状态 | 交付物 | Changes |
|--------|------|--------|---------|
| **M0** | ✅ 完成 | LangChain 文本入账 + Ollama 视觉 | [M0-langchain-text.plan](../Changes/M0-langchain-text.plan)、[M0-ollama-vision.plan](../Changes/M0-ollama-vision.plan) |
| **M1** | ✅ 完成 | FastAPI + PostgreSQL CRUD | — |
| **M2** | ⬜ 待做 | Function Calling 记一笔 / 查账 | — |
| **M3** | ⬜ 待做 | 聊天前端 | — |
| **M4** | ⬜ 待做 | LangGraph Agent | — |
| **M5** | ⬜ 待做 | 文件导入 | — |
| **M6** | ⬜ 待做 | RAG 知识库 | — |
| **M7** | ⬜ 待做 | Embeddings 语义搜账 | — |
| **M8** | ⬜ 待做 | 月报工作流 | — |
| **M9** | ⬜ 待做 | Memory + HITL | — |
| **M10** | ⬜ 待做 | Eval + LangSmith | — |
| **M11** | ⬜ 待做 | Skills 模块 | — |
| **M12** | ⬜ 待做 | Fine-tuning | — |
| **M13** | ⬜ 待做 | 前端仪表盘 | — |

## M0 要点

- 文本链：`examples/00_hello_chain.py` + `common/llm/`
- 视觉链：`examples/01_image_ollama_chain/`
- 解析结构：`ParsedTransaction`（[`server/model/request/parsed.py`](../../server/model/request/parsed.py)）

## M1 要点

- 服务端：[`server/`](../../server/)
- 三表：`categories`、`budgets`、`transactions`
- HTTP 集成测试：[`server/test/`](../../server/test/)
- 规范：本 harness Rules + Skills

## M2+ 启动前

1. 读 [architecture.md](architecture.md) 了解 Agent 接入点
2. 新后端表走 [entity-service](../Skills/entity-service/SKILL.md)（完整流程）或 [add-server-model](../Skills/add-server-model/SKILL.md)（精简 checklist）
3. 新 API 走 [add-api-endpoint](../Skills/add-api-endpoint/SKILL.md)
4. 在 [Changes/](../Changes/) 创建 `M{n}-{slug}.plan` 交付单

## 新建交付单

命名：`M{n}-{slug}.plan`，例如 `M2-function-calling.plan`。

完成后可在文件头加 YAML frontmatter：

```yaml
---
status: done
---
```
