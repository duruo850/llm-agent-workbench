---
name: entity-service
description: 实体服务全栈 SOP — model / request / response / service / db 迁移 / api / 集成测试（参考 Category / Budget / Transaction）
---

# entity-service — 实体服务全栈实现

BillMind M1 每个实体（Category / Budget / Transaction）都遵循同一套**七层流水线**。新增第 4 个实体时，按本 Skill 从 model 到 test 完整走一遍。

## 何时触发

- 用户要求「加一个实体服务」「像 category 那样做一张表」
- 需要理解 Category / Budget / Transaction 如何串联
- 不确定该改哪些文件、顺序如何

> 若只需快速 checklist，可并行阅读 [add-server-model](../add-server-model/SKILL.md)；本 Skill 提供**完整抽象 + 三档参考对照**。

## 前置条件

- 已读 [Rules/server-backend.md](../../Rules/server-backend.md)、[Rules/naming.md](../../Rules/naming.md)
- PostgreSQL 已启动：`docker compose up -d`
- 选定参考实体（见下表）

## 三档参考实现

| 档位 | 实体 | 特点 | 参考文件 |
|------|------|------|----------|
| **A 标准** | Category | 纯 FastCRUD，无自定义 API | 全层最简 |
| **B 关联** | Budget | 外键 `category_id`、唯一约束、索引 | 有 FK 时参照 |
| **C 扩展** | Transaction | 禁用 FastCRUD 列表 + 自定义 `GET /transactions?month=` | 需非标准查询时参照 |

### 各层文件对照

| 层 | Category | Budget | Transaction |
|----|----------|--------|-------------|
| ORM | `model/category.py` | `model/budget.py` | `model/transaction.py` |
| Request | `request/category.py` | `request/budget.py` | `request/transaction.py` |
| Response | `response/category.py` | `response/budget.py` | `response/transaction.py` |
| FastCRUD 实例 | `service/enter.py` | 同上 | 同上 |
| Service | `service/category.py` | `service/budget.py` | `service/transaction.py` |
| API Router | `api/categories.py` | `api/budgets.py` | `api/transactions.py` |
| 路由注册 | `routers.py` | 同上 | 同上 |
| 迁移 | `alembic/versions/001_*.py` | 同上 | 同上 |
| 启动同步 | `db/migrate.py` `_REQUIRED_TABLES` | 同上 | 同上 |
| 测试 | `api/{entities}_test.py` | `api/budgets_test.py` | `api/transactions_test.py` |

## 分层数据流

```mermaid
flowchart TB
  subgraph http [HTTP]
    Client[httpx / curl]
  end

  subgraph app [server/]
    Main[main.py register_routers]
    Routers[routers.py 路由注册表]
    API[api/{entities}.py APIRouter]
    Service[service/{entity}.py 增删改查]
    Req[model/request/*Request]
    Res[model/response/*Response]
    ORM[model/{entity}.py SQLModel]
    FastCRUD[service/enter.py]
    Session[db/session.py get_db]
    Migrate[db/migrate.py]
  end

  subgraph db [PostgreSQL]
    Tables[(tables)]
    Alembic[(alembic_version)]
  end

  Client --> Main
  Main --> Routers
  Routers --> API
  API --> Service
  API --> Req
  API --> Res
  Service --> FastCRUD
  FastCRUD --> ORM
  Service --> Session
  Session --> Tables
  Migrate --> Alembic
  Migrate --> Tables
  ORM -.-> Migrate
```

## 步骤清单（新实体 `{entity}`）

### ① Model — ORM 表定义

- [ ] 新建 `server/model/{entity}.py`
- [ ] `class {Entity}(SQLModel, table=True)`，**无 `*Table` 后缀**
- [ ] 定义 `__tablename__`、字段、`__table_args__`（索引 / 唯一约束 / 外键）
- [ ] 需要 FK 时：`Field(foreign_key="categories.id")`（参照 Budget），**不用 Relationship**

```python
# 参照 server/model/category.py — 最简
class Category(SQLModel, table=True):
    __tablename__ = "categories"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, unique=True)
```

### ② Request — 入参 schema

- [ ] 新建 `server/model/request/{entity}.py`
- [ ] `{Entity}CreateRequest(RequestBase)` — POST body
- [ ] `{Entity}UpdateRequest(RequestBase)` — PATCH body（字段均可选）
- [ ] `{Entity}ListQueryRequest(RequestBase)` — 列表 query（可为空 `pass`）
- [ ] 在 `server/model/request/__init__.py` 导出

基类：[`server/model/base.py`](../../../server/model/base.py) 的 `RequestBase`（`extra="forbid"`）。

### ③ Response — 出参 schema

- [ ] 新建 `server/model/response/{entity}.py`
- [ ] `{Entity}GetResponse` — FastCRUD `select_schema`（仅标量，无 Relationship）
- [ ] 可选：`CreateResponse` / `UpdateResponse` / `ListResponse`（与现有三实体保持一致）
- [ ] `model_config = ConfigDict(from_attributes=True)`
- [ ] 在 `server/model/response/__init__.py` 导出

### ④ Service — 业务层 + enter.py

- [ ] `server/service/enter.py`：添加 `{entity}_crud = FastCRUD({Entity})`
- [ ] 新建 `server/service/{entity}.py`，类名 `{Entity}Service`
- [ ] 实现：`create_{entity}` / `get_{entity}` / `list_{entities}` / `update_{entity}` / `delete_{entity}`
- [ ] 第一参数 `db: AsyncSession`；内部调 `enter.py` 中的 FastCRUD 实例
- [ ] 模块末尾：`{entity}_service = {Entity}Service()`
- [ ] 自定义查询（如 Transaction 按月列表）作为 Service 额外方法

参照 [`server/service/category.py`](../../../server/service/category.py)。

### ⑤ API Router — HTTP 编排 + 路由注册

**5a. 新建 `server/api/{entities}.py`**

- [ ] 定义 `router = APIRouter(prefix="/{entities}", tags=["{entities}"])`
- [ ] 标准五路由：`POST ""` / `GET "/{id}"` / `GET ""` / `PATCH "/{id}"` / `DELETE "/{id}"`
- [ ] 每 handler：`Depends(get_db)` → 调 `{entity}_service` 对应方法
- [ ] 404：service 返回 `None` 时 `HTTPException(404)`；DELETE 成功返回 `204`

参照 [`server/api/categories.py`](../../../server/api/categories.py)。

**5b. 注册到 [`server/routers.py`](../../../server/routers.py)**

- [ ] `from server.api import {entities}`（或追加到现有 import）
- [ ] 在 `register_routers(app)` 内增加：`app.include_router({entities}.router)`

```python
# server/routers.py — 新增实体后追加一行
from server.api import categories, budgets, transactions, tags  # 示例

def register_routers(app: FastAPI) -> None:
    app.include_router(categories.router)
    ...
    app.include_router(tags.router)  # 新实体
```

> `main.py` 只调用 `register_routers(app)`，**不要**在 `main.py` 里直接 `include_router`。

档位 C 自定义列表（如 Transaction `GET ?month=`）仍在同一 `api/{entities}.py` 的 `GET ""` handler 中，逻辑委托给 Service 额外方法。

Transaction 示例：[`server/api/transactions.py`](../../../server/api/transactions.py)。

### ⑥ DB — 迁移与启动同步

- [ ] `server/alembic/versions/NNN_{slug}.py` — `upgrade` / `downgrade` 与 ORM 一致
- [ ] 核心表：更新 `server/db/migrate.py` 的 `_REQUIRED_TABLES`
- [ ] 在 `migrate_on_startup` 中 import 新 model（见 migrate.py 现有三行 import）
- [ ] 启动 `python server/main.py` → lifespan 自动 `alembic upgrade head`

详见 [db-migrate](../db-migrate/SKILL.md)。

### ⑦ Test — HTTP 集成测试

- [ ] 新建 `server/api/{entities}_test.py`（与 `api/{entities}.py` 同目录）
- [ ] 五用例：create / get / list / update / delete
- [ ] 有自定义 API 时追加用例（如 `test_list_transactions_by_month`）
- [ ] 需要依赖时扩展 `server/api/conftest.py` fixture（Budget 依赖 category）
- [ ] `response.raise_for_status()` + 标准 `assert`；PATCH 后 GET 校验

详见 [http-integration-test](../http-integration-test/SKILL.md)。

## 档位选择

```
新实体 {Entity}
    │
    ├─ 仅标准 CRUD，无特殊列表？
    │       └─ 档位 A（参照 Category）
    │
    ├─ 有外键 / 唯一约束？
    │       └─ 档位 B（参照 Budget）+ 档位 A 步骤
    │
    └─ 列表或查询逻辑非默认分页？
            └─ 档位 C（参照 Transaction）= Service 额外方法 + 同一 api router
```

## 整合点（勿漏）

| 文件 | 动作 |
|------|------|
| `server/service/enter.py` | 添加 `{entity}_crud` |
| `server/service/{entity}.py` | `{Entity}Service` + `{entity}_service` 单例 |
| `server/api/{entities}.py` | 定义 `router`，五路由调 service |
| **`server/routers.py`** | **`register_routers` 中 `include_router`** |
| `server/model/request/__init__.py` | 导出 Request |
| `server/model/response/__init__.py` | 导出 Response |
| `server/db/migrate.py` | `_REQUIRED_TABLES` + model import |

## 文件清单模板

以新增 `Tag` 为例（档位 A）：

```
server/model/tag.py
server/model/request/tag.py
server/model/response/tag.py
server/model/request/__init__.py          # 修改
server/model/response/__init__.py         # 修改
server/service/enter.py                   # 修改
server/service/tag.py                     # 新建
server/api/tags.py                        # 新建
server/routers.py                         # include_router
server/alembic/versions/002_add_tags.py   # 新建
server/db/migrate.py                      # 修改 _REQUIRED_TABLES + import
server/api/tags_test.py                     # 新建
server/api/conftest.py                      # 按需 fixture
```

## 验收

```bash
docker compose up -d
python server/main.py

# 另开终端 — 单实体
pytest server/api/tags_test.py -v

# 全量
pytest server/api -v

# 手动
curl http://127.0.0.1:8000/{entities}
curl -X POST http://127.0.0.1:8000/{entities} -H 'Content-Type: application/json' -d '{...}'
```

## 反模式

- 不要在 ORM 上加双向 `Relationship`
- 不要把 SQL / FastCRUD 调用写进 `server/api/`（必须经 Service）
- 不要跳过 Alembic 或 `_REQUIRED_TABLES`
- 不要用 `TestClient`；必须真实 HTTP 集成测试
- 不要 Response 继承带关联的 ORM 类

## 相关 Skill

| Skill | 用途 |
|-------|------|
| [add-server-model](../add-server-model/SKILL.md) | 精简版步骤 checklist |
| [add-api-endpoint](../add-api-endpoint/SKILL.md) | 仅自定义 API 层 |
| [db-migrate](../db-migrate/SKILL.md) | 迁移细节 |
| [http-integration-test](../http-integration-test/SKILL.md) | 测试 SOP |
| [local-dev](../local-dev/SKILL.md) | 本地启动与调试 |
