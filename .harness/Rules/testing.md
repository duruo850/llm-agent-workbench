# testing — HTTP 集成测试

## 目录与运行方式

- **任意目录** 的 `*_test.py` 均可被 pytest / IDE 发现（[`pytest.ini`](../../pytest.ini)：`testpaths = .`）
- HTTP 集成测试与路由同目录：[`server/api/`](../../server/api/)
- 单元 / MCP 等：如 [`agent/mcp/gaode/*_test.py`](../../agent/mcp/gaode/)、[`utils/*_test.py`](../../utils/)
- **真实 HTTP** 打已启动的 `main`（**不用** FastAPI `TestClient`）
- 全量：`pytest -v`；仅 API：`pytest server/api -v`（须先 `python server/main.py`）

## 文件组织

**一 model、一 API、一 test**：同一业务实体（或同一 API 路由模块）的 HTTP 集成测试合并到单个 `{entity}_test.py`，**不要**为同一 `server/api/{entity}.py` 再拆 `{feature}_test.py`（例如 `POST /transactions/import` 归入 `transactions_test.py`，而非 `transactions_import_test.py`）。

每 API 模块独立测试文件：

| 文件 | 覆盖 |
|------|------|
| `account_test.py` | 登录、401、账号隔离 |
| `categories_test.py` | Category CRUD |
| `budgets_test.py` | Budget CRUD |
| `transactions_test.py` | Transaction CRUD、按月列表、CSV 导入 |
| `agent_test.py` | Agent `/agent/chat`（真实 LLM） |
| `health_test.py` | `/health` |
| `conftest.py` | 共用 fixture |

执行全量测试见 [Skills/http-integration-test/SKILL.md](../Skills/http-integration-test/SKILL.md) § B。

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
| `require_llm` | 未配置 `DEEPSEEK_API_KEY` 则 `pytest.skip`（仅 Agent 测试） |

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
- **不要**使用 `unittest.mock` / `@patch`（含 mock LLM）；Agent 等需走真实 HTTP + 真实外部依赖，缺 Key 用 `require_llm` skip
- 金额比较注意 `Decimal` 序列化可能是字符串 `"2000.00"` 或数字

## 自定义 API 测试

- 新增路由挂在已有 `server/api/{entity}.py` 时，**追加用例到** `{entity}_test.py`（见上方「一 model、一 API、一 test」）
- `GET /transactions?month=2025-06` — 返回数组，非 `{data: ...}`
- `GET /summary/monthly?month=2025-06` — 跨实体汇总，独立 `summary_test.py`（对应 `summary.py`，非 transaction 子路由）

## 调试

- F5：`.vscode/launch.json` — **Debug pytest (current file)** 或 **Debug Test**（须 API 已启动）
- 环境变量 `API_BASE_URL` 可改端口

## 跳过条件

API 未启动时相关用例 `pytest.skip`，并提示：

```
请先运行: python server/main.py
```

Agent 测试未配置 `DEEPSEEK_API_KEY` 时 `require_llm` fixture 会 skip。

详见 [Skills/http-integration-test/SKILL.md](../Skills/http-integration-test/SKILL.md)。
