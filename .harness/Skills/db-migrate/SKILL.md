---
name: db-migrate
description: Alembic 迁移编写与 migrate_on_startup 行为
---

# db-migrate — 数据库迁移

## 何时触发

- 新增/修改表结构
- 空库首次启动
- 用户问「怎么迁移」「alembic upgrade」

## 前置条件

- PostgreSQL 运行中：`docker compose up -d`（根目录 [`docker-compose.yml`](../../../docker-compose.yml)）
- `DATABASE_URL` 已在 `.env` 配置

## 步骤清单

- [ ] 1. 修改 `server/model/*.py` SQLModel 定义
- [ ] 2. 在 `server/alembic/versions/` 手写 revision（参考 `001_initial_schema.py`）
- [ ] 3. 确保 `upgrade()` 与 `downgrade()` 对称
- [ ] 4. 若新核心表，更新 `server/db/migrate.py` 的 `_REQUIRED_TABLES`
- [ ] 5. 启动 `python server/main.py` — lifespan 自动 `alembic upgrade head`
- [ ] 6. 或手动：`alembic -c server/alembic.ini upgrade head`

## migrate_on_startup 行为

[`server/db/migrate.py`](../../../server/db/migrate.py)：

1. 连接数据库，检查 `_REQUIRED_TABLES` 是否齐全
2. 已就绪 → 日志 `database schema ready`，跳过
3. 未就绪 → 自动执行 `alembic upgrade head`
4. 库不可达 → 启动失败

## 文件清单

| 路径 | 操作 |
|------|------|
| `server/model/*.py` | 表定义 |
| `server/alembic/versions/*.py` | revision |
| `server/db/migrate.py` | `_REQUIRED_TABLES` |
| `server/alembic.ini` | 通常无需改 |
| `common/env.py` | `DATABASE_URL` |

## 验收

```bash
docker compose up -d
python server/main.py
# 日志应含 database schema ready 或 running alembic upgrade head

# 手动验证
alembic -c server/alembic.ini current
alembic -c server/alembic.ini upgrade head
```

## 空库流程

```bash
docker compose down -v   # 慎用：清空数据
docker compose up -d
python server/main.py    # 自动建表
curl http://127.0.0.1:8000/health
```

## 反模式

- 不要用 `server/docker-compose.yml`（已废弃，用根目录 compose）
- 不要手动改 PostgreSQL 表而不写 revision
- 不要忘记在 `migrate_on_startup` 前 import 新 model（见 `migrate.py` 中的 model import）
