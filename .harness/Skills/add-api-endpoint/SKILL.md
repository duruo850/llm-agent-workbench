---
name: add-api-endpoint
description: 添加自定义 FastAPI 路由（非标准 CRUD 走 server/api/）
---

# add-api-endpoint — 添加自定义 API

## 何时触发

- 需要非 FastCRUD 标准 CRUD 的查询（按月列表、聚合汇总、复杂 join）
- 用户说「加一个 API」「按月查账」「月度汇总」

## 前置条件

- 已读 [Rules/server-backend.md](../../Rules/server-backend.md)
- 确认**不能**用 FastCRUD 配置解决（标准 CRUD 走 `crud_router`）

## 步骤清单

- [ ] 1. 判断：标准 CRUD → 用 FastCRUD；自定义查询 → `server/api/`
- [ ] 2. 在 `server/model/request/` 定义 Query 参数模型（如 `*QueryRequest`）
- [ ] 3. 在 `server/model/response/` 定义返回模型
- [ ] 4. 在 `server/api/{feature}.py` 创建 `APIRouter`
- [ ] 5. 使用 `Depends(get_db)` 注入 session；复用 `server/crud/instances.py` 的 crud 实例
- [ ] 6. 在 `server/main.py` 中 `app.include_router(router)`
- [ ] 7. 非 API 逻辑放 `utils/`（如 [`utils/date_range.py`](../../../utils/date_range.py)）
- [ ] 8. 在 `server/test/` 添加 HTTP 集成测试

## 文件清单

| 路径 | 操作 |
|------|------|
| `server/api/{feature}.py` | 新建/修改 |
| `server/model/request/*.py` | Query 模型 |
| `server/model/response/*.py` | 响应模型 |
| `server/main.py` | `include_router` |
| `server/test/test_*.py` | 测试 |

## 验收

```bash
python server/main.py
curl 'http://127.0.0.1:8000/transactions?month=2025-06'
curl 'http://127.0.0.1:8000/summary/monthly?month=2025-06'
pytest server/test -v -k summary
```

## 参考实现

- [`server/api/transactions.py`](../../../server/api/transactions.py) — 按月列表
- [`server/api/summary.py`](../../../server/api/summary.py) — 月度汇总

## 反模式

- 不要在 `server/api/` 重复实现 POST/PATCH/DELETE（已由 FastCRUD 提供）
- 不要把 `utils/` 逻辑内联到路由 handler 若可复用
- 不要与 FastCRUD 路由路径冲突（如重复注册 `GET /transactions` 需注意顺序）
