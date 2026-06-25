# server/ 服务端详解（M1）

## 启动顺序

```bash
# 1. 依赖
pip install -r requirements.txt
cp .env.example .env

# 2. 数据库
docker compose up -d

# 3. API（自动迁移）
python server/main.py
# 或 uvicorn server.main:app --reload --port 8000
```

详见 [Skills/local-dev/SKILL.md](../Skills/local-dev/SKILL.md)。

## 日志

启动后每条请求输出：

```
HH:MM:SS INFO [billmind.request] GET /health -> 200 (1.2ms)
```

数据库迁移日志 logger：`billmind.db`。

## API 列表

### 健康检查

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | `{"status":"ok"}` |

### Category（FastCRUD）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/categories` | 创建 |
| GET | `/categories/{id}` | 单条 |
| GET | `/categories` | 列表 `{data: [...]}` |
| PATCH | `/categories/{id}` | 更新（可能空 body） |
| DELETE | `/categories/{id}` | 删除 |

### Budget（FastCRUD）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/budgets` | 创建 |
| GET | `/budgets/{id}` | 单条 |
| GET | `/budgets` | 列表 |
| PATCH | `/budgets/{id}` | 更新 |
| DELETE | `/budgets/{id}` | 删除 |

### Transaction

| 方法 | 路径 | 提供方 | 说明 |
|------|------|--------|------|
| POST | `/transactions` | FastCRUD | 记一笔 |
| GET | `/transactions/{id}` | FastCRUD | 单条 |
| PATCH | `/transactions/{id}` | FastCRUD | 更新 |
| DELETE | `/transactions/{id}` | FastCRUD | 删除 |
| GET | `/transactions?month=` | 自定义 api/ | 按月列表 |

> FastCRUD 对 transaction 禁用了 `read_multi`（`deleted_methods=["read_multi"]`），列表走自定义路由。

### Summary（自定义）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/summary/monthly?month=YYYY-MM` | 分类汇总 + 预算对比 |

## 示例 curl

```bash
curl http://127.0.0.1:8000/health

curl -X POST http://127.0.0.1:8000/categories \
  -H 'Content-Type: application/json' \
  -d '{"name":"餐饮","budget_monthly":2000}'

curl -X POST http://127.0.0.1:8000/transactions \
  -H 'Content-Type: application/json' \
  -d '{"amount":38,"category":"餐饮","merchant":"Starbucks","note":"","transacted_at":"2025-06-25T12:00:00"}'

curl 'http://127.0.0.1:8000/transactions?month=2025-06'
curl 'http://127.0.0.1:8000/summary/monthly?month=2025-06'
```

## 测试

```bash
python server/main.py          # 终端 1
pytest server/test -v          # 终端 2
```

## 核心文件

| 文件 | 职责 |
|------|------|
| [`main.py`](../../server/main.py) | FastAPI 入口、中间件、异常、路由注册 |
| [`crud/routers.py`](../../server/crud/routers.py) | FastCRUD 路由 |
| [`api/transactions.py`](../../server/api/transactions.py) | 按月查账 |
| [`api/summary.py`](../../server/api/summary.py) | 月度汇总 |
| [`db/migrate.py`](../../server/db/migrate.py) | 启动迁移 |
| [`db/session.py`](../../server/db/session.py) | 异步 engine + get_db |

## 相关

- [architecture.md](architecture.md)
- [Rules/server-backend.md](../Rules/server-backend.md)
