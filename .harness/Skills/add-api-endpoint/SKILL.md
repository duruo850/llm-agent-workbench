---
name: add-api-endpoint
description: 添加 FastAPI 路由 — HTTP 编排层，业务逻辑走 server/service/
---

# add-api-endpoint — 添加 API 路由

## 何时触发

- 需要新增或扩展 HTTP 接口（标准 CRUD、按月列表、聚合汇总）
- 用户说「加一个 API」「按月查账」「月度汇总」

## 前置条件

- 已读 [Rules/server-backend.md](../../Rules/server-backend.md)
- 业务逻辑已在 [`server/service/`](../../../server/service/) 实现（或同步新建 Service 方法）

## 步骤清单

- [ ] 1. 在 `server/service/{entity}.py` 添加或扩展 Service 方法（含 SQL / FastCRUD 调用）
- [ ] 2. 在 `server/model/request/` 定义 Query / Body 模型
- [ ] 3. 在 `server/model/response/` 定义返回模型
- [ ] 4. 在 `server/api/{feature}.py` 创建 `APIRouter`，**只调 service**
- [ ] 5. 使用 `Depends(get_db)` 注入 session，传给 service 第一参数
- [ ] 6. 在 `server/main.py` 中 `app.include_router(router)`
- [ ] 7. 可复用的通用逻辑放 `utils/`
- [ ] 8. 在 `server/api/` 添加 `{feature}_test.py` 集成测试

## 文件清单

| 路径 | 操作 |
|------|------|
| `server/service/{entity}.py` | Service 方法 |
| `server/api/{feature}.py` | 新建/修改 |
| `server/model/request/*.py` | Query 模型 |
| `server/model/response/*.py` | 响应模型 |
| `server/main.py` | `include_router` |
| `server/api/{feature}_test.py` | 测试 |

## 验收

```bash
python server/main.py
curl 'http://127.0.0.1:8000/transactions?month=2025-06'
curl 'http://127.0.0.1:8000/summary/monthly?month=2025-06'
pytest server/api -v -k summary
```

## 参考实现

- [`server/api/categories.py`](../../../server/api/categories.py) — 标准 CRUD → `category_service`
- [`server/api/transactions.py`](../../../server/api/transactions.py) — 含按月列表
- [`server/api/summary.py`](../../../server/api/summary.py) — 月度汇总

## 反模式

- 不要在 `server/api/` 直接调 FastCRUD 或写 SQL
- 不要把可复用的 `utils/` 逻辑内联到路由 handler
- 不要新建 `server/services/`（目录为 **`server/service/`**）
