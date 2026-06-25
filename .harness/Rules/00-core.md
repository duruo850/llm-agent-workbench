# 00 — 全局原则

BillMind 仓库内所有 Agent 与贡献者应遵守的通用约定。

## 最小改动

- 只改与任务直接相关的文件；不主动改无关 README、文档或配置
- 优先复用现有函数与抽象，不重复造轮子
- 注释只解释非显而易见的业务逻辑，代码本身应自解释
- 尽量采用增量修改形式，最小改动

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

- 服务端代码在 [`server/`](../../server/)
- 共享 LLM / 环境在 [`common/`](../../common/)
- 非 API 工具函数在 [`utils/`](../../utils/)
- 示例在 [`examples/`](../../examples/)

## 与 learning-plan 的关系

- [`docs/learning-plan.md`](../../docs/learning-plan.md) = 长期课表（理想态结构）；**以本 harness + 实际代码为准**
- 里程碑进度见 [Wiki/milestones.md](../Wiki/milestones.md)

## 入口

实现任何功能前必须先读 [`.harness/README.md`](../README.md)。

## 新任务检查清单

1. 读对应 Skill 的「步骤清单」
2. 对照 [Rules/server-backend.md](server-backend.md) 确认分层
3. 按 Skill「验收」运行 pytest 或 curl
4. 若新增核心表，更新 [`migrate.py`](../../server/db/migrate.py) 的 `_REQUIRED_TABLES`
5. 若涉及新里程碑，在 [Changes/](../Changes/) 创建或更新交付单

## 禁止

- 不创建 `.cursor/rules` 或 `.cursor/skills`（规范仅 `.harness` + 根 [`AGENTS.md`](../../AGENTS.md)）
- 不硬编码 API Key 或数据库密码
- 不在 ORM 上恢复双向 `Relationship`
