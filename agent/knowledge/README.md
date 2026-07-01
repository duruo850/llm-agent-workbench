# BillMind 知识库（RAG）

理财类静态 Markdown，供 `agent/storage/rag` 索引到 Milvus。

| 目录 | 含义 | kb 标识 |
|------|------|---------|
| `finance/` | 理财知识 | `finance` |

共 10 篇，文件名 `01_*.md` … `10_*.md`。frontmatter 含 `title` 与 `kb`。

## 更新内容后重建索引

**一键入库**（推荐）：

```bash
.venv/bin/python3.14 -m agent.storage.rag.knowledge_index
```

或手动：

```bash
docker compose up -d ollama ollama-pull-embeddings   # 启动 Ollama 并自动 pull embedding 模型
# 或手动：
.venv/bin/python3.14 -m agent.storage.rag.knowledge_index                                  # 一键入库（含上述步骤）
```

服务启动时若集合为空也会自动索引（需 Milvus + Ollama 可用）。
