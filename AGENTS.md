# BillMind Agent 指南

实现本仓库任何功能前，**必须先阅读** [`.harness/README.md`](.harness/README.md)。

## 快速入口

| 任务 | 阅读 |
|------|------|
| 了解全局原则 | [Rules/00-core.md](.harness/Rules/00-core.md) |
| **新增完整实体服务**（参照 Category/Budget/Transaction） | [Skills/entity-service/SKILL.md](.harness/Skills/entity-service/SKILL.md) |
| 新增数据库表 + CRUD（精简 checklist） | [Skills/add-server-model/SKILL.md](.harness/Skills/add-server-model/SKILL.md) |
| 添加自定义 API | [Skills/add-api-endpoint/SKILL.md](.harness/Skills/add-api-endpoint/SKILL.md) |
| 写 HTTP 集成测试 | [Skills/http-integration-test/SKILL.md](.harness/Skills/http-integration-test/SKILL.md) |
| 数据库迁移 | [Skills/db-migrate/SKILL.md](.harness/Skills/db-migrate/SKILL.md) |
| 本地开发 / 调试 | [Skills/local-dev/SKILL.md](.harness/Skills/local-dev/SKILL.md) |

## 禁止

- 绕过 harness 自创目录或命名（如 `backend/schemas/`、`CategoryTable`）
- 在 ORM 模型上恢复双向 `Relationship`
- 用户未要求时 `git commit`

## 背景

- 架构：[Wiki/architecture.md](.harness/Wiki/architecture.md)
- 目录：[Wiki/repo-layout.md](.harness/Wiki/repo-layout.md)
- 里程碑：[Wiki/milestones.md](.harness/Wiki/milestones.md)
- 交付单：[Changes/](.harness/Changes/)

## 环境

- Python：`.venv/bin/python3.14`
- 配置：`common/env.py` + 根目录 `.env`
- 数据库：根目录 `docker compose up -d` → `python server/main.py`
