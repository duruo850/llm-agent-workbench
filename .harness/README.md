# BillMind Harness

Agent 实现 BillMind 功能前的**必读入口**。本目录沉淀目录结构、命名、分层、测试、数据库与本地开发约定，避免各里程碑代码风格漂移。

## 阅读顺序

1. **[Rules/00-core.md](Rules/00-core.md)** — 全局原则（最小 diff、中文、不擅自 commit）
2. 按任务类型查 **Rules** 专项规范
3. 按任务类型执行 **Skills** 中的 SOP
4. 需要背景时查 **Wiki**
5. 里程碑交付单见 **Changes**

## 四层结构

| 层 | 目录 | 用途 |
|----|------|------|
| Rules | [Rules/](Rules/) | 必须遵守的编码规范 |
| Skills | [Skills/](Skills/) | 可执行 SOP（加表、加 API、写测试等） |
| Wiki | [Wiki/](Wiki/) | 架构、目录、服务端现状说明 |
| Changes | [Changes/](Changes/) | 里程碑可执行交付单 |

## 按任务查 Skill

| 用户意图 / 场景 | Skill |
|-----------------|-------|
| **新增完整实体服务**（model→service→db→test 全流程） | [Skills/entity-service/SKILL.md](Skills/entity-service/SKILL.md) |
| 新增数据库表 + CRUD（精简 checklist） | [Skills/add-server-model/SKILL.md](Skills/add-server-model/SKILL.md) |
| 加自定义 API 路由 | [Skills/add-api-endpoint/SKILL.md](Skills/add-api-endpoint/SKILL.md) |
| 写 / 跑 HTTP 集成测试 | [Skills/http-integration-test/SKILL.md](Skills/http-integration-test/SKILL.md) |
| 数据库迁移 | [Skills/db-migrate/SKILL.md](Skills/db-migrate/SKILL.md) |
| 本地开发 / 调试 | [Skills/local-dev/SKILL.md](Skills/local-dev/SKILL.md) |
| **定 plan 并实现功能**（Changes + milestones 同步） | [Skills/implement-plan/SKILL.md](Skills/implement-plan/SKILL.md) |
| **提取 AI 知识点 / 写 docs/knowledge** | [Skills/extract-ai-knowledge/SKILL.md](Skills/extract-ai-knowledge/SKILL.md) |

### Skill 选择（30 秒）

```
实现某个功能 / 里程碑           → implement-plan（先写 M{n}_{seq}.plan）
实现 AI 里程碑（M0/M2/M4/…）    → implement-plan + extract-ai-knowledge（验收含 docs/knowledge/）
新实体（像 Category/...）       → entity-service（首选）
  ├─ 仅改表结构                    → db-migrate
  ├─ 实体已有，加自定义查询         → add-api-endpoint
  └─ 补测试 / 跑测试 / 验收 API    → http-integration-test

跑不起来 / 首次搭环境              → local-dev
```

## Rules 索引

- [Rules/00-core.md](Rules/00-core.md) — 全局原则
- [Rules/server-backend.md](Rules/server-backend.md) — `server/` 分层与 FastCRUD
- [Rules/naming.md](Rules/naming.md) — 命名表
- [Rules/testing.md](Rules/testing.md) — HTTP 集成测试

## Wiki 索引

- [Wiki/architecture.md](Wiki/architecture.md) — Web / Server / Agent / PostgreSQL 整体架构（**只读，Agent 不得修改**）
- [Wiki/repo-layout.md](Wiki/repo-layout.md) — 实际目录 vs learning-plan
- [Wiki/server.md](Wiki/server.md) — 服务端启动、API、中间件
- [Wiki/milestones.md](Wiki/milestones.md) — M0–M13 进度索引

## 禁止

- 绕过 harness 自创目录或命名（如 `backend/schemas/`、`CategoryTable`）
- 在 ORM 模型上恢复双向 `Relationship`（曾导致 SQLAlchemy 2 映射 500）
- **修改** [Wiki/architecture.md](Wiki/architecture.md)（整体架构由用户维护）
- 未读 Rules/Skills 就直接改 `server/` 核心结构
