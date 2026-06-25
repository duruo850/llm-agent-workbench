# BillMind Server (M1)

FastAPI + PostgreSQL 记账 REST API。CRUD 由 **SQLAlchemy + FastCRUD** 自动生成，与 `src/` 共用领域模型与环境配置。

## 前置

- Python 3.11+
- Docker（PostgreSQL）

## 启动

```bash
# 1. 安装依赖（项目根目录）
pip install -r requirements.txt

# 2. 配置数据库连接
cp .env.example .env
# 确认 DATABASE_URL 已设置

# 3. 启动 PostgreSQL
docker compose -f server/docker-compose.yml up -d

# 4. 数据库迁移
alembic -c server/alembic.ini upgrade head

# 5. （可选）默认分类
python -m server.seed

# 6. 启动 API
uvicorn server.main:app --reload --port 8000
```

## 验收 curl

```bash
# 健康检查
curl http://localhost:8000/health

# 创建分类
curl -X POST http://localhost:8000/categories -H 'Content-Type: application/json' \
  -d '{"name":"餐饮","budget_monthly":2000}'

# 创建预算
curl -X POST http://localhost:8000/budgets -H 'Content-Type: application/json' \
  -d '{"category_id":1,"month":"2025-06","limit_amount":2000}'

# 记一笔
curl -X POST http://localhost:8000/transactions -H 'Content-Type: application/json' \
  -d '{"amount":38,"category":"餐饮","merchant":"Starbucks","note":"","transacted_at":"2025-06-25T12:00:00"}'

# 按月查账
curl 'http://localhost:8000/transactions?month=2025-06'

# 月度汇总
curl 'http://localhost:8000/summary/monthly?month=2025-06'

# 更新 / 删除
curl -X PATCH http://localhost:8000/transactions/1 -H 'Content-Type: application/json' -d '{"note":"午餐"}'
curl -X DELETE http://localhost:8000/transactions/1
```

## 目录

```
server/
├── main.py              # FastAPI 入口
├── routers.py           # 路由注册
├── api/                 # HTTP 编排
├── service/             # 业务 Service + enter.py（FastCRUD 实例）
├── db/                  # session + 迁移
├── model/
│   ├── transaction.py
│   ├── category.py
│   ├── budget.py
│   ├── request/
│   └── response/
└── alembic/
```

**架构**：`server/model/` 定义 ORM → `server/service/` 业务逻辑 → `server/api/` HTTP 编排。

与 `src/` 的协作：

- `common/env.py` — 共享 `.env` 加载与 `DATABASE_URL`
- `server/model/transaction.py` 等 — `Transaction`（Pydantic 实体）+ `TransactionTable`（SQLAlchemy 表）
- `server/model/request/` — `*Request`；`request/parsed.py` 为 LLM 解析
- `server/model/response/` — `*Response`（含月度汇总等无表结构）

> 实际数据库为 **PostgreSQL**（`asyncpg`），非 learning-plan 中的 MySQL。
