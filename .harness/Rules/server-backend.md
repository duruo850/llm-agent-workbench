# server/ 后端分层与 Service 约定

M1 服务端 (`server/`) 层职责

| 层 | 位置 | 约定 |
|----|------|------|
| ORM + 表实体 | [`server/model/{entity}.py`](../../server/model/category.py) | SQLModel `table=True`，类名 `Category` / `Budget` / `Transaction`（**无 Table 后缀**） |
| 请求体 | [`server/model/request/`](../../server/model/request/) | `*CreateRequest` / `*UpdateRequest` / `*QueryRequest` |
| 响应体 | [`server/model/response/`](../../server/model/response/) | 标量字段 `*Response` / `*GetResponse`；**不继承**带 Relationship 的 ORM |
| **Service** | [`server/service/{entity}.py`](../../server/service/category.py) | 每 model 一个 `{Entity}Service`，实现增删改查 + 领域查询 |
| FastCRUD 实例 | [`server/service/enter.py`](../../server/service/enter.py) | `{entity}_crud`，**仅 Service 层调用** |
| HTTP API | [`server/api/`](../../server/api/) | 只做 HTTP 编排：`Depends(get_db)` → 调 service → 返回 Response |
| 数据库 | [`server/db/`](../../server/db/) | `session.py` + [`migrate.py`](../../server/db/migrate.py) 启动自动 `alembic upgrade head` |
| 工具函数 | [`utils/`](../../utils/) | **通用**可复用纯函数（日期、集合索引等） |
| 迁移 | [`server/alembic/`](../../server/alembic/) | revision 文件放在 `versions/` |

## 数据流

```
HTTP 请求 → server/api/{entity}.py → server/service/{entity}.py → service/enter.py → PostgreSQL
Agent 工具 → server/service/{entity}.py（注入 AsyncSession，不经 HTTP）
```

## Service 层（参照 Gin-Vue-Admin `ClassService` 模式）

每个实体一个 Service 类 + 模块级单例 `{entity}_service`：

| 方法 | 说明 |
|------|------|
| `create_{entity}` | 创建记录 |
| `get_{entity}` | 按 id 查询，不存在返回 `None` |
| `list_{entities}` | 列表（标准实体返回 `PaginatedList`） |
| `update_{entity}` | 部分更新 |
| `delete_{entity}` | 删除，返回是否成功 |

示例：[`server/service/category.py`](../../server/service/category.py)、[`server/service/account.py`](../../server/service/account.py)（含 CRUD + `login_or_register` 等领域方法）

- Service **接收** `db: AsyncSession` 为第一参数，由 API `Depends(get_db)` 或 Agent 调用方注入
- 复杂查询（按月列表、月度汇总）放在对应 Service 的额外方法中
- **禁止**在 `server/api/` 写 SQL / 直接调 FastCRUD

## API 层

[`server/api/categories.py`](../../server/api/categories.py) — 标准 CRUD 模板  
[`server/api/transactions.py`](../../server/api/transactions.py) — 含自定义 `GET ?month=`、`POST /import`  
[`server/api/summary.py`](../../server/api/summary.py) — 跨实体汇总

- HTTP 集成测试与 API 模块 **1:1**：`server/api/{entity}.py` → `server/api/{entity}_test.py`（同一实体的全部路由写在同一 test 文件，见 [testing.md](testing.md)）

- 404：`service` 返回 `None` 时 `raise HTTPException(404)`
- 列表分页：Query `offset` / `limit`，响应 `PaginatedList[{Entity}ListResponse]`

## 数据库 session

- 异步引擎：[`server/db/session.py`](../../server/db/session.py)
- `get_db` 作为 FastAPI `Depends` 注入
- URL 来自 [`common/env.py`](../../common/env.py) 的 `get_database_url()`

## 启动迁移

[`server/db/migrate.py`](../../server/db/migrate.py)：

- `migrate_on_startup(engine)` 在 `lifespan` 中调用
- 核心表 `_REQUIRED_TABLES` — `("accounts", "categories", "budgets", "transactions")`
- 新核心表需同步更新此元组

## IntegrityError → 409

[`server/main.py`](../../server/main.py) 将 `IntegrityError` 映射为 HTTP 409，区分 unique / foreign key 等场景。

## 禁止

- **禁止**在 ORM 模型上恢复 SQLAlchemy 2 双向 `Relationship`
- 需要关联用 `category_id` 外键 + 查询 join，不用 ORM `Relationship`
- 禁止在 `server/model/` 放 SQLAlchemy 裸 `Column` 定义而不用 SQLModel Field
- **禁止**在 `server/api/` 直接调 FastCRUD 或写 SQL（必须经 Service）

## 新增实体检查清单

1. `server/model/{entity}.py` — SQLModel 表
2. `server/alembic/versions/` — 新 revision
3. `server/model/response/{entity}.py` — `*GetResponse` / `*ListResponse`
4. `server/model/request/{entity}.py` — Create / Update / Query
5. `server/service/enter.py` — 注册 `{entity}_crud = FastCRUD({Entity})`
6. **`server/service/{entity}.py`** — `{Entity}Service` 增删改查
7. **`server/api/{entities}.py`** — HTTP 路由调 service
8. 若为核心表，更新 [`migrate.py`](../../server/db/migrate.py) 的 `_REQUIRED_TABLES`

详见 [Skills/entity-service/SKILL.md](../Skills/entity-service/SKILL.md)。
