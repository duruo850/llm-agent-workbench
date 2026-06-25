# testing — HTTP 集成测试

## 目录与运行方式

- 测试目录：[`server/test/`](../../server/test/)
- **真实 HTTP** 打已启动的 `main`（**不用** FastAPI `TestClient`）
- 先起 `python server/main.py`，再 `pytest server/test -v`
- [`pytest.ini`](../../pytest.ini) 含 `-s` 显示 `print`；`pythonpath = .`

## 文件组织

每 model 独立文件：

| 文件 | 覆盖 |
|------|------|
| `test_category.py` | Category CRUD |
| `test_budget.py` | Budget CRUD |
| `test_transaction.py` | Transaction + 自定义列表 |
| `test_health.py` | `/health` |
| `conftest.py` | 共用 fixture |

## conftest 链

| Fixture | 作用 |
|---------|------|
| `api_base_url` | 默认 `http://127.0.0.1:8000`，可 `API_BASE_URL` 环境变量覆盖 |
| `require_api` | 未启动则 `pytest.skip` |
| `http_client` | `httpx.Client` |
| `unique_suffix` | 避免重名 |
| `category` | 创建分类并在 teardown 删除 |
| `budget` | 依赖 category |
| `transaction` | 依赖 category |

## 每表五用例模板

1. **create** — POST，断言 body 字段
2. **get** — GET `/{id}`
3. **list** — GET 列表
4. **update** — PATCH 后 GET 确认（因 PATCH 可能空 body）
5. **delete** — DELETE 后 GET 404

## 断言风格

```python
response.raise_for_status()
assert body["name"] == expected
```

- **不要**封装自定义 `assert_*` helper
- **不要**在测试里用 `TestClient`
- 金额比较注意 `Decimal` 序列化可能是字符串 `"2000.00"` 或数字

## 自定义 API 测试

- `GET /transactions?month=2025-06` — 返回数组，非 `{data: ...}`
- `GET /summary/monthly?month=2025-06` — 见 `test_transaction.py` 或专门测试

## 调试

- F5：`.vscode/launch.json` — **Debug pytest (current file)** 或 **Debug Test**（须 API 已启动）
- 环境变量 `API_BASE_URL` 可改端口

## 跳过条件

API 未启动时相关用例 `pytest.skip`，并提示：

```
请先运行: python server/main.py
```

详见 [Skills/http-integration-test/SKILL.md](../Skills/http-integration-test/SKILL.md)。
