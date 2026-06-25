---
name: extract-ai-knowledge
description: 从 BillMind 代码与 learning-plan 提取 AI 技术知识点，写入 docs/knowledge/{slug}.md
---

# extract-ai-knowledge — 提取 AI 知识点文档

从项目代码与 [learning-plan](../../../docs/learning-plan.md) 提炼某主题的**本质**（非课表），写入 `docs/knowledge/{slug}.md`，并更新索引。

## 何时触发

- 用户说「提取知识点」「写 function calling 讲解」「整理 RAG 知识文档」
- 某里程碑完成后，需要一篇「讲本质 + 映射代码」的深度文档
- 用户指向 `docs/knowledge/` 或本 Skill 名称
- AI的Skill没有存储下来的时候就新增

**不触发**（直接改业务代码即可）：

- 纯实现功能、无文档需求
- 只改 typo 或单行 bugfix

## 前置条件

1. 已读 [Rules/00-core.md](../../Rules/00-core.md)（中文、最小 diff）
2. 读 [docs/learning-plan.md](../../../docs/learning-plan.md) 中对应里程碑章节
3. 读项目内相关代码（见下方 slug 表的「典型代码路径」）
4. 参考已完成样例：[docs/knowledge/function-calling.md](../../../docs/knowledge/function-calling.md)

## 主题 slug 表

与 learning-plan 里程碑对齐；`status` 指 `docs/knowledge/README.md` 索引中的状态。

| slug | 主题 | 里程碑 | 典型代码路径 | 状态 |
|------|------|--------|-------------|------|
| `langchain-basics` | LangChain LCEL / Prompt / Chain | M0 | `examples/00_hello_chain.py`, `common/llm/` | 待提取 |
| `function-calling` | Function Calling | M2 | `agent/runner.py`, `agent/tools/` | done |
| `langgraph` | LangGraph 状态图 Agent | M4 | `agent/graph.py`（待建） | 待提取 |
| `rag` | RAG / LlamaIndex | M6 | `indexer/`（待建） | 待提取 |
| `embeddings` | Embeddings 语义检索 | M7 | 待建 | 待提取 |
| `memory-hitl` | Memory + Human-in-the-loop | M9 | 待建 | 待提取 |
| `eval-langsmith` | Eval + LangSmith | M10 | 待建 | 待提取 |
| `agent-skills` | 可插拔 Agent Skills | M11 | `agent/skills/`（待建） | 待提取 |
| `fine-tuning` | Fine-tuning / LoRA | M12 | 待建 | 待提取 |

## 输出路径

| 产出 | 路径 |
|------|------|
| 知识点正文 | `docs/knowledge/{slug}.md` |
| 索引更新 | `docs/knowledge/README.md`（对应行 status → done） |
| 可选反向链接 | `docs/learning-plan.md` 对应里程碑节末加「详见 docs/knowledge/{slug}.md」 |

## 文档模板（固定章节）

复制 [template.md](template.md) 填充，章节顺序不变：

1. **一句话本质** — 该技术在 BillMind 中的角色
2. **常见误解 vs 本质** — 表格，至少 2 行
3. **核心流程** — 分步说明；**至少 1 张 mermaid**（sequence 或 flowchart）
4. **关键概念** — 术语表
5. **与相邻技术对比** — 如 M0 vs M2、Chain vs Agent
6. **BillMind 代码对照表** — 步骤 ↔ 文件/函数/消息类型；引用**真实路径**
7. **常见误区** — 工程实践中易错点
8. **官方文档** — LangChain / LangGraph / LlamaIndex 等链接
9. **里程碑与延伸阅读** — 链到 learning-plan、knowledge 索引

## 单篇提取步骤清单

```
[ ] 1. Research
      - 读 learning-plan 对应 M{n} 节
      - 读 slug 表中的代码路径（含 runner、tools、examples、server API）
      - 确认里程碑在 .harness/Wiki/milestones.md 的状态

[ ] 2. 写 docs/knowledge/{slug}.md
      - 按 template 章节填充
      - 代码引用用仓库内真实路径与行号（或模块 docstring）
      - 至少 1 张 mermaid

[ ] 3. 更新 docs/knowledge/README.md
      - 对应主题 status → done
      - 代码入口列填实际路径

[ ] 4. 可选：learning-plan.md 对应节末加反向链接

[ ] 5. 验收（见下）
```

## mermaid 要求

- 每篇至少 **1 张** sequenceDiagram 或 flowchart
- 节点名用 BillMind 实际模块（如 `agent/runner`、`server/M1`）
- 四步类主题（Function Calling、LangGraph 循环）优先用 sequenceDiagram

## 验收

```bash
# 文件存在
ls docs/knowledge/{slug}.md

# 索引已更新
grep {slug} docs/knowledge/README.md

# 内容质量（人工）
# - 含「本质」说明，非泛泛框架介绍
# - 链到真实代码路径
# - 中文、至少 1 张 mermaid
# - 无空章节
```

## 禁止

- 在 `docs/knowledge/` 外另建平行知识目录
- 复制 learning-plan 课表全文（应讲本质 + 代码映射）
- 引用不存在的代码路径（待建路径需标注「待建」）
- 用户未要求时修改 agent 业务逻辑

## 参考

- 已完成样例：[function-calling.md](../../../docs/knowledge/function-calling.md)
- 架构背景（只读）：[Wiki/architecture.md](../../Wiki/architecture.md)
- 空模板：[template.md](template.md)
