# Changes — 里程碑交付单

可执行的里程碑交付单，与 [`docs/learning-plan.md`](../../docs/learning-plan.md)（长期课表）互补。

实现流程见 [Skills/implement-plan/SKILL.md](../Skills/implement-plan/SKILL.md)。

## 命名规范

```
M{n}_{seq}-{slug}.plan
```

| 部分 | 说明 | 示例 |
|------|------|------|
| `n` | 里程碑 0–13 | `M0`、`M2` |
| `seq` | 该里程碑下从 1 递增 | `_1`、`_2`、`_3` |
| `slug` | 短英文 kebab-case | `function-calling` |

示例：`M0_1-langchain-text.plan`、`M2_1-function-calling.plan`

- 新建 plan 复制 [`_template.plan`](_template.plan)
- frontmatter 必填：`milestone`、`seq`、`slug`、`status`、`skills`
- `status`：`draft` → `in_progress` → `done` | `cancelled`

## 索引

| 文件 | 里程碑 | seq | 状态 |
|------|--------|-----|------|
| [M0_1-langchain-text.plan](M0_1-langchain-text.plan) | M0 | 1 | done |
| [M0_2-ollama-vision.plan](M0_2-ollama-vision.plan) | M0 | 2 | done |
| [M2_1-function-calling.plan](M2_1-function-calling.plan) | M2 | 1 | done |
| [M3_1-chat-frontend.plan](M3_1-chat-frontend.plan) | M3 | 1 | done |
| [M4_1-langgraph-agent.plan](M4_1-langgraph-agent.plan) | M4 | 1 | done |
| [M4_2-accounts-auth.plan](M4_2-accounts-auth.plan) | M4 | 2 | done |

> M1 已在 harness 建立前完成，无编号 plan；后续 M1 补丁可用 `M1_1-*.plan`。

## 与 learning-plan 的关系

| 文档 | 角色 |
|------|------|
| `docs/learning-plan.md` | 长期学习路线、理想项目结构 |
| `.harness/Changes/M{n}_{seq}-*.plan` | 单次可交付、可验收的执行单 |
| `.harness/Wiki/milestones.md` | 进度索引，链到本目录 |

## 新建交付单（简要）

1. 读 [implement-plan](../Skills/implement-plan/SKILL.md) 阶段 A
2. 扫描 `M{n}_*.plan` 取 max(seq)+1
3. 从 `_template.plan` 复制并填写
4. 更新本 README 索引 + [milestones.md](../Wiki/milestones.md)
5. 实现完成后 `status: done`，同步 milestones 状态
