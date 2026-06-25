---
name: entity-service
description: 实体服务全栈 SOP — model / request / response / crud / db 迁移 / 自定义 api / 集成测试（参考 Category / Budget / Transaction）
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
| CRUD 实例 | `crud/instances.py` | 同上 | 同上 |
| CRUD 路由 | `crud/routers.py` | 同上 | `deleted_methods=["read_multi"]` |
| 自定义 API | — | — | `api/transactions.py` |
| 迁移 | `alembic/versions/001_*.py` | 同上 | 同上 |
| 启动同步 | `db/migrate.py` `_REQUIRED_TABLES` | 同上 | 同上 + model import |
| 测试 | `test/test_category.py` | `test/test_budget.py` | `test/test_transaction.py` |

## 分层数据流

```mermaid
flowchart TB
  subgraph http [HTTP]
    Client[httpx / curl]
  end

  subgraph app [server/]
    Main[main.py include_router]
    CRUDRouter[crud/routers.py crud_router]
    CustomAPI[api/*.py 可选]
    Req[model/request/*Request]
    Res[model/response/*Response]
    ORM[model/{entity}.py SQLModel]
    FastCRUD[crud/instances.py]
    Session[db/session.py get_db]
    Migrate[db/migrate.py]
  end

  subgraph db [PostgreSQL]
    Tables[(tables)]
    Alembic[(alembic_version)]
  end

  Client --> Main
  Main --> CRUDRouter
  Main --> CustomAPI
  CRUDRouter --> Req
  CRUDRouter --> Res
  CRUDRouter --> FastCRUD
  CustomAPI --> Req
  CustomAPI --> Res
  CustomAPI --> FastCRUD
  FastCRUD --> ORM
  CRUDRouter --> Session
  CustomAPI --> Session
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

### ④ CRUD — FastCRUD 实例与路由

- [ ] `server/crud/instances.py`：`{entity}_crud = FastCRUD({Entity})`
- [ ] `server/crud/routers.py`：注册 `crud_router(...)`
  - `session=get_db`
  - `create_schema` / `update_schema` / `select_schema`
  - `path="/{entities}"`（复数 kebab）
- [ ] 若列表需自定义（如 Transaction）：`deleted_methods=["read_multi"]`

[`server/crud/routers.py`](../../../server/crud/routers.py) 中 Category 为标准模板。

### ⑤ API — 自定义路由（可选，档位 C）

- [ ] 判断：FastCRUD 能否满足列表/查询？不能才加 `server/api/{entity}s.py`
- [ ] 定义 Query Request + List Response
- [ ] `APIRouter(prefix="/{entities}")` + `Depends(get_db)`
- [ ] 复用 `crud/instances.py` 的 crud 实例做 `select`
- [ ] `server/main.py` 中 `app.include_router(router)`

Transaction 示例：[`server/api/transactions.py`](../../../server/api/transactions.py) — `GET ?month=` 返回 `list[...]`，非 `{data: ...}`。

### ⑥ DB — 迁移与启动同步

- [ ] `server/alembic/versions/NNN_{slug}.py` — `upgrade` / `downgrade` 与 ORM 一致
- [ ] 核心表：更新 `server/db/migrate.py` 的 `_REQUIRED_TABLES`
- [ ] 在 `migrate_on_startup` 中 import 新 model（见 migrate.py 现有三行 import）
- [ ] 启动 `python server/main.py` → lifespan 自动 `alembic upgrade head`

详见 [db-migrate](../db-migrate/SKILL.md)。

### ⑦ Test — HTTP 集成测试

- [ ] 新建 `server/test/test_{entity}.py`
- [ ] 五用例：create / get / list / update / delete
- [ ] 有自定义 API 时追加用例（如 `test_list_{entity}s_by_month`）
- [ ] 需要依赖时扩展 `conftest.py` fixture（Budget 依赖 category）
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
    └─ 列表或查询逻辑非 FastCRUD 默认？
            └─ 档位 C（参照 Transaction）= A/B + api/ + deleted_methods
```

## 整合点（勿漏）

| 文件 | 动作 |
|------|------|
| `server/main.py` | `include_router`（crud 路由自动注册；自定义 api 需手动加） |
| `server/db/migrate.py` | `_REQUIRED_TABLES` + model import |
| `server/model/request/__init__.py` | 导出 Request |
| `server/model/response/__init__.py` | 导出 Response |
| `server/crud/instances.py` | FastCRUD 实例 |
| `server/crud/routers.py` | crud_router |

## 文件清单模板

以新增 `Tag` 为例（档位 A）：

```
server/model/tag.py
server/model/request/tag.py
server/model/response/tag.py
server/model/request/__init__.py          # 修改
server/model/response/__init__.py         # 修改
server/crud/instances.py                  # 修改
server/crud/routers.py                    # 修改
server/alembic/versions/002_add_tags.py   # 新建
server/db/migrate.py                      # 修改 _REQUIRED_TABLES + import
server/test/test_tag.py                   # 新建
server/test/conftest.py                   # 按需 fixture
```

## 验收

```bash
docker compose up -d
python server/main.py

# 另开终端 — 单实体
pytest server/test/test_{entity}.py -v

# 全量
pytest server/test -v

# 手动
curl http://127.0.0.1:8000/{entities}
curl -X POST http://127.0.0.1:8000/{entities} -H 'Content-Type: application/json' -d '{...}'
```

## 反模式

- 不要在 ORM 上加双向 `Relationship`
- 不要把标准 CRUD 写进 `server/api/`（应用 FastCRUD）
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
