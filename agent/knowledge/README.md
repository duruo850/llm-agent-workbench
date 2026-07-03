# BillMind 知识库（RAG）

理财类静态 Markdown，供 `storage/rag` 索引到 Milvus。

| 目录 | 含义 | kb 标识 |
|------|------|---------|
| `finance/` | 理财知识 | `finance` |

共 10 篇，文件名 `01_*.md` … `10_*.md`。frontmatter 含 `title` 与 `kb`。

## 更新内容后重建索引

先确保 Ollama（含 embedding 模型）与 Milvus 已启动，再执行：

```bash
# 本地
.venv/bin/python3.14 -m storage.rag.knowledge_index

# Docker（server 镜像内跑，完成后退出）
docker compose --profile rag up knowledge-index
```

服务启动时若集合为空也会自动索引（需 Milvus + Ollama 可用）。
