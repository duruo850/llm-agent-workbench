# 00 — 全局原则

BillMind 仓库内所有 Agent 与贡献者应遵守的通用约定。

## 最小改动

- 只改与任务直接相关的文件；不主动改无关 README、文档或配置
- 优先复用现有函数与抽象，不重复造轮子
- 注释只解释非显而易见的业务逻辑，代码本身应自解释
- 尽量采用增量修改形式，最小改动
- **少于 20 行的逻辑不要单独抽函数**（含 `server/api/` 内私有 helper）；直接内嵌在调用处，除非同一文件内多处复用或逻辑本身足够复杂

## Git

- **用户未明确要求时不 `git commit`等git相关操作**
- 不执行 destructive git 操作（force push、hard reset 等）除非用户明确要求
- 不跳过 pre-commit hooks

## 沟通与文档

- 响应用户使用**中文**
- 代码注释与 harness 文档使用中文

## Python 环境

- 优先使用项目虚拟环境：`.venv/bin/python3.14`（依赖安装在此环境）
- 共享配置：[`common/env.py`](../../common/env.py) + 根目录 [`.env`](../../.env.example)（从 `.env.example` 复制）
- 启动 server 前确保 PostgreSQL 已运行：`docker compose up -d`（根目录 [`docker-compose.yml`](../../docker-compose.yml)）

## 路径约定

| 目录 | 用途 |
|------|------|
| [`server/`](../../server/) | FastAPI 业务 API、ORM、CRUD |
| [`common/`](../../common/) | 环境变量、LLM 客户端等跨模块配置 |
| [`utils/`](../../utils/) | **通用**纯函数（无业务域、可跨 server/agent 复用），如日期解析、`map_by_name` |
| [`agent/`](../../agent/) | Agent 编排与领域工具（`agent.py`、`graph.py`、`skills/`） |
| [`docs/knowledge/`](../../docs/knowledge/) | AI 里程碑知识点沉淀（见下方「AI 知识点」） |
| [`examples/`](../../examples/) | 各阶段独立 demo |

**代码归属**：可复用、与具体 API/Agent 流程无关的逻辑放 `utils/`；不要散落在 `server/api/`、`agent/` 内联实现。参考 [`utils/date_range.py`](../../utils/date_range.py)、[`utils/map_by_name.py`](../../utils/map_by_name.py)。

## 与 learning-plan 的关系

- [`docs/learning-plan.md`](../../docs/learning-plan.md) = 长期课表（理想态结构）；**以本 harness + 实际代码为准**
- 里程碑进度见 [Wiki/milestones.md](../Wiki/milestones.md)

## 入口

实现任何功能前必须先读 [`.harness/README.md`](../README.md)。

## AI 知识点

凡 **AI 里程碑**（M0、M2、M4、M6–M12；涉及 `agent/`、`common/llm/`、`indexer/`、`examples/` 中 Agent 类 demo）引入的新概念，实现完成时**必须**沉淀到 [`docs/knowledge/{slug}.md`](../../docs/knowledge/)，并更新 [`docs/knowledge/README.md`](../../docs/knowledge/README.md) 索引为 `done`。

- 执行流程：与 [implement-plan](Skills/implement-plan/SKILL.md) 阶段 B 同步，按 [extract-ai-knowledge](Skills/extract-ai-knowledge/SKILL.md) 撰写
- plan frontmatter `skills` 须含 `extract-ai-knowledge`；plan 正文须有「知识点文档」章节
- 无对应 slug 时，先在 `docs/knowledge/README.md` 索引中新增行再写正文

## 新任务检查清单

1. 读对应 Skill 的「步骤清单」
2. 对照 [Rules/server-backend.md](server-backend.md) 确认分层
3. 按 Skill「验收」运行 pytest 或 curl
4. 若新增核心表，更新 [`migrate.py`](../../server/db/migrate.py) 的 `_REQUIRED_TABLES`
5. 若涉及新里程碑，用 [implement-plan](Skills/implement-plan/SKILL.md) 创建 `M{n}_{seq}-*.plan`
6. 若为 AI 里程碑：按 [extract-ai-knowledge](Skills/extract-ai-knowledge/SKILL.md) 更新 `docs/knowledge/`，并在 plan 阶段 C 验收

## 禁止

- 不创建 `.cursor/rules` 或 `.cursor/skills`（规范仅 `.harness` + 根 [`AGENTS.md`](../../AGENTS.md)）
- **不得修改** [Wiki/architecture.md](../Wiki/architecture.md)（整体架构由用户维护；实现细节写 [server.md](../Wiki/server.md) 或 [repo-layout.md](../Wiki/repo-layout.md)）
- 不硬编码 API Key 或数据库密码
- 不在 ORM 上恢复双向 `Relationship`
