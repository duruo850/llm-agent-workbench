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

### Category（`api/categories` → `service/category`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/categories` | 创建 |
| GET | `/categories/{id}` | 单条 |
| GET | `/categories` | 列表 `{data, total_count}` |
| PATCH | `/categories/{id}` | 更新 |
| DELETE | `/categories/{id}` | 删除（204） |

### Budget（`api/budgets` → `service/budget`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/budgets` | 创建 |
| GET | `/budgets/{id}` | 单条 |
| GET | `/budgets` | 列表 |
| PATCH | `/budgets/{id}` | 更新 |
| DELETE | `/budgets/{id}` | 删除（204） |

### Transaction（`api/transactions` → `service/transaction`）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/transactions` | 记一笔 |
| GET | `/transactions/{id}` | 单条 |
| PATCH | `/transactions/{id}` | 更新 |
| DELETE | `/transactions/{id}` | 删除（204） |
| GET | `/transactions?month=` | 按月列表（数组） |

### Summary（`api/summary` → `service/transaction`）

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
pytest server/api -v          # 终端 2
```

## 核心文件

| 文件 | 职责 |
|------|------|
| [`main.py`](../../server/main.py) | FastAPI 入口、中间件、异常、路由注册 |
| [`service/{entity}.py`](../../server/service/category.py) | 业务 Service（增删改查） |
| [`api/{entities}.py`](../../server/api/categories.py) | HTTP 编排，调 Service |
| [`service/enter.py`](../../server/service/enter.py) | FastCRUD 实例（Service 内部使用） |
| [`db/migrate.py`](../../server/db/migrate.py) | 启动迁移 |
| [`db/session.py`](../../server/db/session.py) | 异步 engine + get_db |

## 相关

- [architecture.md](architecture.md)
- [Rules/server-backend.md](../Rules/server-backend.md)
