---
name: add-server-model
description: 新增 server 数据库表：SQLModel + Alembic + Request/Response + FastCRUD 路由
---

# add-server-model — 新增数据库表

> 完整七层流程（含三档参考对照）见 [entity-service](../entity-service/SKILL.md)。本 Skill 为精简 checklist。

## 何时触发

- 用户要求「加一张表」「新增实体」「tags / accounts 表」等
- 里程碑 M1+ 需要持久化新领域对象

## 前置条件

- 已读 [Rules/00-core.md](../../Rules/00-core.md)、[Rules/server-backend.md](../../Rules/server-backend.md)、[Rules/naming.md](../../Rules/naming.md)
- PostgreSQL 已启动（`docker compose up -d`）
- 参考现有 [`Category`](../../../server/model/category.py) 实现

## 步骤清单

- [ ] 1. 在 `server/model/{entity}.py` 定义 SQLModel `table=True` 实体（无 `*Table` 后缀）
- [ ] 2. 在 `server/alembic/versions/` 新建 Alembic revision（`upgrade` / `downgrade`）
- [ ] 3. 在 `server/model/response/{entity}.py` 添加 `{Entity}GetResponse`（仅标量字段）
- [ ] 4. 在 `server/model/request/{entity}.py` 添加 `CreateRequest` / `UpdateRequest`
- [ ] 5. 在 `server/model/request/__init__.py` 与 `response/__init__.py` 导出
- [ ] 6. 在 `server/crud/instances.py` 添加 `FastCRUD(Entity)`
- [ ] 7. 在 `server/crud/routers.py` 注册 `crud_router`
- [ ] 8. 若为核心业务表，更新 `server/db/migrate.py` 的 `_REQUIRED_TABLES`
- [ ] 9. 在 `server/test/test_{entity}.py` 写五用例 CRUD 测试
- [ ] 10. 启动 `python server/main.py` 验证迁移 + pytest

## 文件清单

| 路径 | 操作 |
|------|------|
| `server/model/{entity}.py` | 新建/修改 |
| `server/alembic/versions/NNN_*.py` | 新建 |
| `server/model/response/{entity}.py` | 新建 |
| `server/model/request/{entity}.py` | 新建 |
| `server/crud/instances.py` | 修改 |
| `server/crud/routers.py` | 修改 |
| `server/db/migrate.py` | 修改（核心表） |
| `server/test/test_{entity}.py` | 新建 |

## 验收

```bash
docker compose up -d
python server/main.py
# 另开终端
pytest server/test/test_{entity}.py -v
curl http://127.0.0.1:8000/{entities}
```

## 反模式

- 不要在 ORM 上加 `Relationship` 双向关联
- 不要用 `CategoryTable` 命名
- 不要把 CRUD 逻辑写进 `server/api/`
- 不要跳过 Alembic revision 直接改表
- 不要用 `TestClient` 代替 HTTP 集成测试
