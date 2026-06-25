# server/ 后端分层与 FastCRUD 约定

M1 服务端 (`server/`) 层职责

| 层 | 位置 | 约定 |
|----|------|------|
| ORM + 表实体 | [`server/model/{entity}.py`](../../server/model/category.py) | SQLModel `table=True`，类名 `Category` / `Budget` / `Transaction`（**无 Table 后缀**） |
| 请求体 | [`server/model/request/`](../../server/model/request/) | `*CreateRequest` / `*UpdateRequest` / `*QueryRequest` |
| 响应体 | [`server/model/response/`](../../server/model/response/) | 标量字段 `*Response` / `*GetResponse`；**不继承**带 Relationship 的 ORM |
| CRUD | [`server/crud/`](../../server/crud/) | FastCRUD 实例 + [`crud/routers.py`](../../server/crud/routers.py) 的 `crud_router` |
| 自定义 API | [`server/api/`](../../server/api/) | 仅**非标准**查询（如按月列表、月度汇总） |
| 数据库 | [`server/db/`](../../server/db/) | `session.py` + [`migrate.py`](../../server/db/migrate.py) 启动自动 `alembic upgrade head` |
| 工具函数 | [`utils/`](../../utils/) | 非 API 专用逻辑不放 `server/api/` |
| 迁移 | [`server/alembic/`](../../server/alembic/) | revision 文件放在 `versions/` |

## FastCRUD 路由

标准 CRUD 由 [`server/crud/routers.py`](../../server/crud/routers.py) 的 `crud_router` 生成：

```python
category_router = crud_router(
    session=get_db,
    model=Category,
    crud=category_crud,
    create_schema=CategoryCreateRequest,
    update_schema=CategoryUpdateRequest,
    select_schema=CategoryGetResponse,
    path="/categories",
    tags=["categories"],
)
```

- `select_schema` 用 `*GetResponse`（如 `CategoryGetResponse`），避免返回 ORM 全字段 + 关联
- 自定义路由在 [`server/api/`](../../server/api/) 并在 [`main.py`](../../server/main.py) `include_router`

## 自定义 API 示例

[`server/api/transactions.py`](../../server/api/transactions.py) — `GET /transactions?month=YYYY-MM` 按月过滤  
[`server/api/summary.py`](../../server/api/summary.py) — `GET /summary/monthly?month=YYYY-MM` 月度汇总

## 数据库 session

- 异步引擎：[`server/db/session.py`](../../server/db/session.py)
- `get_db` 作为 FastAPI `Depends` 注入
- URL 来自 [`common/env.py`](../../common/env.py) 的 `get_database_url()`

## 启动迁移

[`server/db/migrate.py`](../../server/db/migrate.py)：

- `migrate_on_startup(engine)` 在 `lifespan` 中调用
- 核心表 `_REQUIRED_TABLES` — `("categories", "budgets", "transactions")`
- 新核心表需同步更新此元组

## IntegrityError → 409

[`server/main.py`](../../server/main.py) 将 `IntegrityError` 映射为 HTTP 409，区分 unique / foreign key 等场景。

## 禁止

- **禁止**在 ORM 模型上恢复 SQLAlchemy 2 双向 `Relationship`（曾导致 SQLAlchemy 2 映射 500
- 需要关联用 `category_id` 外键 + 查询 join，不用 ORM `Relationship`
- 禁止在 `server/model/` 放 SQLAlchemy 裸 `Column` 定义而不用 SQLModel Field
- 禁止把 CRUD 逻辑塞进 `server/api/`（应用层只做 HTTP 编排）

## 与 learning-plan 差异

| learning-plan | 实际 |
|---------------|------|
| `backend/` | [`server/`](../../server/) |
| MySQL | PostgreSQL + `asyncpg` |
| `schemas/` | `server/model/request/` + `response/` |
| `TransactionTable` | `Transaction`（SQLModel table=True） |
| 手动迁移 | 启动 `main` 自动迁移（仍可用 `alembic -c server/alembic.ini upgrade head`） |

## 新增实体检查清单

1. `server/model/{entity}.py` — SQLModel 表
2. `server/alembic/versions/` — 新 revision
3. `server/model/response/{entity}.py` — `*GetResponse`
4. `server/model/request/{entity}.py` — Create / Update / Query
5. `server/crud/instances.py` + `routers.py`
6. 若为核心表，更新 [`migrate.py`](../../server/db/migrate.py) 的 `_REQUIRED_TABLES`
7. 需要自定义查询时再加 `server/api/`

详见 [Skills/add-server-model/SKILL.md](../Skills/add-server-model/SKILL.md)。
