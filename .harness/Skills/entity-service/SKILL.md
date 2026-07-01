---
name: entity-service
description: 实体服务全栈 SOP — model / request / response / service / db 迁移 / api / 集成测试（参考 Category / ChatMessage 薄 CRUD）
---

# entity-service — 实体服务全栈实现

BillMind M1 实体 (Category / Budget / Transaction) 采用 **Request/Response 穿透 Service** (档位 A–C).  
M9 起 Chat History (`Conversation` / `ChatMessage`) 采用 **薄 CRUD + ORM 进出 Service** (档位 E).  
**新实体默认档位 E** — Service 复制 [service.py.tpl](service.py.tpl) 即可, 详见下文.

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
| **D 租户根** | Account | 无 `account_id` 自引用; HTTP 以 `/auth/login` 为主 | [`storage/postgres/service/account.py`](../../../storage/postgres/service/account.py) |
| **E 薄 CRUD** | ChatMessage | Service 入出 ORM; Request/Response 仅 API | [service.py.tpl](service.py.tpl) / [`chat_message.py`](../../../storage/postgres/service/chat_message.py) |

> **档位 A–D (M1 存量)**: `create_` / `get_` / `list_` / `update_` / `delete_`, 入出 Request/Response.  
> **档位 E (新实体默认)**: 复制 [service.py.tpl](service.py.tpl) → `storage/postgres/service/{entity}.py`; 复杂逻辑放 API/Facade.

### 各层文件对照

| 层 | Category (A) | ChatMessage (E) | Conversation (E) |
|----|--------------|-----------------|------------------|
| ORM | `model/category.py` | `model/chat_message.py` | `model/conversation.py` |
| Request | `request/category.py` | `request/chat_message.py` | `request/conversation.py` |
| Response | `response/category.py` | `response/chat_message.py` | `response/conversation.py` |
| FastCRUD | `storage/postgres/service/enter.py` | `chat_message_crud` | `conversation_crud` |
| Service | `storage/postgres/service/category.py` | `storage/postgres/service/chat_message.py` | `storage/postgres/service/conversation.py` |
| API | `api/categories.py` | `api/chat_messages.py` | `api/conversations.py` |
| 测试 | `api/categories_test.py` | `api/chat_messages_test.py` | `api/conversations_test.py` |

## 档位 E — 薄 CRUD Service

**新实体默认本档位.** Service 层只做薄 CRUD (入出 ORM, 委托 FastCRUD); Request/Response 转换与多实体编排放 **API** 或 **Agent Facade**, 不写进 Service.

实现方式: 复制 [service.py.tpl](service.py.tpl) 为 `storage/postgres/service/{entity}.py`, 替换 `{Entity}` / `{entity}` 及 `get_list` 过滤键. 细节以模板与标杆 [`chat_message.py`](../../../storage/postgres/service/chat_message.py) / [`conversation.py`](../../../storage/postgres/service/conversation.py) 为准.

**`get_list` 约定** (档位 E):

- 入参 `{Entity}ListQueryRequest` (含 `Page` / `PageSize` 默认值 + 可选过滤字段)
- Service 内组装 `filters: dict[str, object]`, 非空字段才写入; 分页 `offset=req.Page * req.PageSize`, `limit=req.PageSize`
- API 用 `Depends()` 解析 query, 租户字段 (如 `AccountId`) 由 handler 注入: `req = query.model_copy(update={"AccountId": account.id})`

编排参考: [`chat_messages.py`](../../../server/api/chat_messages.py)、[`conversation.py`](../../../storage/postgres/service/conversation.py)（`create_chat_messages`）.

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

**档位 A–D** (M1 存量):

- [ ] `{Entity}CreateRequest` / `UpdateRequest` — 逐字段展开
- [ ] `{Entity}ListQueryRequest` — 列表 query: `Page`/`PageSize` 默认值 + 可选过滤字段 (PascalCase); 标杆 [`request/conversation.py`](../../../server/model/request/conversation.py)
- [ ] 参照 [`request/category.py`](../../../server/model/request/category.py)

**档位 E** (新实体默认):

- [ ] 复制 [request.py.tpl](request.py.tpl) → Create/Update 用 `Data: {Entity}`
- [ ] API 从 `body.Data` 组装 ORM 后调 service; 标杆 [`request/chat_message.py`](../../../server/model/request/chat_message.py)

### ③ Response — 出参 schema

**档位 A–D** (M1 存量):

- [ ] `{Entity}GetResponse` + 可选 `CreateResponse` / `UpdateResponse` / `ListResponse`
- [ ] 参照 [`response/category.py`](../../../server/model/response/category.py)

**档位 E** (新实体默认):

- [ ] 复制 [response.py.tpl](response.py.tpl) → `{Entity}GetListResponse` 含 `List: list[{Entity}]`
- [ ] GET 列表 `return {Entity}GetListResponse(List=result.data)`; POST/PATCH `status_code=200` 无 body
- [ ] 标杆: [`response/chat_message.py`](../../../server/model/response/chat_message.py)

### ④ Service — 业务层 + enter.py

**档位 A–D** (M1 存量):

- [ ] `storage/postgres/service/enter.py`: `{entity}_crud = FastCRUD({Entity})`
- [ ] `create_{entity}` / `get_{entity}` / `list_{entities}` / `update_{entity}` / `delete_{entity}`
- [ ] 入参 Request, 出参 Response
- [ ] 参照 [`storage/postgres/service/category.py`](../../../storage/postgres/service/category.py)

**档位 E** (新实体默认):

- [ ] `enter.py` 注册 `{entity}_crud`; Service 复制 [service.py.tpl](service.py.tpl), `get_list(db, req)` 用 filters + 分页
- [ ] API 做 Request/Response 转换与编排; 参照 [`conversations.py`](../../../server/api/conversations.py)、[`chat_messages.py`](../../../server/api/chat_messages.py)

### ⑤ API Router — HTTP 编排 + 路由注册

**5a. 新建 `server/api/{entities}.py`**

档位 A–D: 标准五路由, handler 调 `{entity}_service`, 入参 Request / 出参 Response.

档位 E: Handler 内 Request → ORM → `service.*` → `Response.model_validate`; 编排见 [档位 E](#档位-e--薄-crud-service).

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
    ├─ M9+ 新表 / 新实体?
    │       └─ 档位 E — 复制 [service.py.tpl](service.py.tpl)
    │
    ├─ 仅标准 CRUD, 无特殊列表? (M1 存量风格)
    │       └─ 档位 A (参照 Category)
    │
    ├─ 有外键 / 唯一约束?
    │       └─ 档位 B (参照 Budget) + 档位 A 或 E 步骤
    │
    ├─ 列表或查询逻辑非默认分页?
    │       └─ 档位 C (参照 Transaction) = API/Service 额外方法
    │
    └─ 租户根 / 认证实体?
            └─ 档位 D (参照 Account)
```

## 整合点（勿漏）

| 文件 | 动作 |
|------|------|
| `storage/postgres/service/enter.py` | 添加 `{entity}_crud` |
| `storage/postgres/service/{entity}.py` | `{Entity}Service` + `{entity}_service` 单例 |
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
storage/postgres/service/enter.py           # 修改
storage/postgres/service/tag.py             # 新建
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
- 不要把 SQL / FastCRUD 调用写进 `server/api/` (必须经 Service)
- 档位 E: 不要把 Request/Response 传入 Service; 不要把跨实体编排写进 Service
- 不要跳过 Alembic 或 `_REQUIRED_TABLES`
- 不要用 `TestClient`；必须真实 HTTP 集成测试
- 不要 Response 继承带关联的 ORM 类
- 不要因「只有 login 接口」而省略 Service 层 CRUD（见档位 D / Account）

## 相关 Skill

| Skill | 用途 |
|-------|------|
| [add-server-model](../add-server-model/SKILL.md) | 精简版步骤 checklist |
| [add-api-endpoint](../add-api-endpoint/SKILL.md) | 仅自定义 API 层 |
| [db-migrate](../db-migrate/SKILL.md) | 迁移细节 |
| [http-integration-test](../http-integration-test/SKILL.md) | 测试 SOP |
| [local-dev](../local-dev/SKILL.md) | 本地启动与调试 |
| [service.py.tpl](service.py.tpl) | 档位 E Service 复制模板 |
| [request.py.tpl](request.py.tpl) | 档位 E Request 复制模板 |
| [response.py.tpl](response.py.tpl) | 档位 E Response 复制模板 |
