# Changes — 里程碑交付单

可执行的里程碑交付单，与 [`docs/learning-plan.md`](../../docs/learning-plan.md)（长期课表）互补。

## 命名规范

- 格式：`M{n}-{slug}.plan`
- 示例：`M2-function-calling.plan`、`M5-file-import.plan`
- 完成后可在文件头加 frontmatter：`status: done`

## 索引

| 文件 | 里程碑 | 状态 |
|------|--------|------|
| [M0-langchain-text.plan](M0-langchain-text.plan) | M0 文本入账链 | done |
| [M0-ollama-vision.plan](M0-ollama-vision.plan) | M0+ Ollama 视觉 | done |

## 与 learning-plan 的关系

| 文档 | 角色 |
|------|------|
| `docs/learning-plan.md` | 长期学习路线、理想项目结构 |
| `.harness/Changes/*.plan` | 单次可交付、可验收的执行单 |
| `.harness/Wiki/milestones.md` | 进度索引，链到本目录 |

## 新建交付单

1. 复制已有 `.plan` 作为模板
2. 填写里程碑、交付文件、验收标准、运行命令
3. 在 [milestones.md](../Wiki/milestones.md) 添加链接
4. 实现完成后标记 `status: done`
