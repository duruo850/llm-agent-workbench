---
name: http-integration-test
description: server/api HTTP 集成测试 SOP（编写 *_test.py + Agent 起 main.py 跑全量 pytest）
---

# http-integration-test — HTTP 集成测试

## 何时触发

- 新增/修改 API 需要**写**测试
- 用户要求「写测试」「加 *_test.py」
- 用户要求「测试一下」「跑测试」「验收 API」「pytest」「集成测试全跑一遍」

## 前置条件

- 已读 [Rules/testing.md](../../Rules/testing.md)
- Python：`.venv/bin/python3.14`
- PostgreSQL 已起：`docker compose up -d`（根目录）
- `.env` 含有效 `DATABASE_URL`

---

## A. 编写测试

### 命名与位置

- 测试与 API **同目录**：`server/api/{entity}_test.py`
- **一 model、一 API、一 test**：`server/api/{entity}.py` 的全部路由（含 CRUD 与自定义端点如 `/import`）写入同一 `{entity}_test.py`；禁止为同一 API 模块再建 `{entity}_{feature}_test.py`
- 示例：`categories.py` → `categories_test.py`；`transactions.py`（含 `/import`）→ `transactions_test.py`
- 共用 fixture：`server/api/conftest.py`
- 测试 helper（非 fixture）：`common/test/`（如 `common/test/account.py` 登录封装）

### 步骤清单

- [ ] 1. 确认 `server/api/conftest.py` fixture 可用（`http_client`、`category` 等）
- [ ] 2. 新建或扩展 `server/api/{entity}_test.py`（与 API 模块 1:1；每路由模块一文件）
- [ ] 3. 实现五用例：create / get / list / update / delete（健康检查等例外见 `health_test.py`）
- [ ] 4. 使用 `response.raise_for_status()` + 标准 `assert`
- [ ] 5. PATCH 后用 GET 验证（PATCH 可能空 body）
- [ ] 6. 分页列表断言：`assert "data" in body`
- [ ] 7. 自定义 API 断言返回形状（如 Transaction 按月列表为 `list`）
- [ ] 8. 执行验收 → 见下方 **B. 跑测试**

### 文件清单

| 路径 | 操作 |
|------|------|
| `server/api/conftest.py` | 按需扩展 fixture |
| `server/api/{entity}_test.py` | 新建或扩展（同一 API 模块勿拆多文件） |
| `common/test/` | 共用 helper（登录、Bearer header 等） |
| `pytest.ini` | `testpaths = server/api`，`python_files = *_test.py` |

### 模板

参考 [`server/api/categories_test.py`](../../../server/api/categories_test.py)：

```python
def test_create_category(http_client: httpx.Client, unique_suffix: str) -> None:
    response = http_client.post("/categories", json={"name": f"新建-{unique_suffix}"})
    response.raise_for_status()
    body = response.json()
    assert body["name"] == ...
    http_client.delete(f"/categories/{body['id']}")
```

登录 / 401 参考 [`server/api/account_test.py`](../../../server/api/account_test.py)；Agent 真实 LLM 参考 [`server/api/agent_test.py`](../../../server/api/agent_test.py)（无 mock，依赖 `DEEPSEEK_API_KEY`）。

---

## B. 跑测试（Agent 执行）

用户要求测试时，**Agent 自行在终端完成**，不要只贴命令让用户手动跑。

- [ ] **1. 检查 API 是否已在跑**

```bash
curl -sf http://127.0.0.1:8000/health
```

- 成功 → 跳到步骤 3
- 失败 → 继续步骤 2

- [ ] **2. 后台启动 API**

```bash
.venv/bin/python3.14 server/main.py
```

- 使用 Shell 工具 **`block_until_ms: 0`** 放后台
- 轮询 `/health`（最多 ~30s），直到 200
- 仍失败：读终端输出，排查 Docker / DB / 迁移 / 端口占用，修复后重试

- [ ] **3. 跑全部 API 集成测试**

```bash
.venv/bin/python3.14 -m pytest server/api -v
```

- 默认 `pytest.ini` 已限定 `testpaths = server/api`、`*_test.py`
- **不要**只跑单个文件，除非用户明确指定

- [ ] **4. 汇报结果**

汇总：**passed / failed / skipped / error** 数量；失败用例名与断言/状态码；skip 原因（API 未起、无 `DEEPSEEK_API_KEY` 等）

- [ ] **5. 失败时**

修代码或环境 → 从步骤 3 重跑（API 仍活着则不必重启）；不要 `git commit`（除非用户要求）

- [ ] **6. 收尾（可选）**

步骤 2 由 Agent 起的 `main.py`：**默认保持运行**；用户明确要求关闭时再 kill 进程

### 测试文件清单（须全覆盖）

| 文件 | 说明 | 可能 skip |
|------|------|-----------|
| `health_test.py` | `/health` | API 未起 |
| `account_test.py` | 登录、401、账号隔离 | API 未起 |
| `categories_test.py` | Category CRUD | API 未起 |
| `budgets_test.py` | Budget CRUD | API 未起 |
| `transactions_test.py` | Transaction CRUD、按月、CSV 导入 | API 未起 |
| `agent_test.py` | `/agent/chat` 真实 LLM | 无 `DEEPSEEK_API_KEY` 或 API 未起 |

### 环境变量

| 变量 | 作用 |
|------|------|
| `API_BASE_URL` | 默认 `http://127.0.0.1:8000`，与 conftest 一致 |
| `DEEPSEEK_API_KEY` | 配置后 `agent_test.py` 才会执行（非 skip） |

### 验收标准

- `pytest server/api -v` exit code **0**
- 无 **failed / error**（**skipped** 可接受：Agent 测试缺 Key 时常见）
- 用户若要求「全绿含 Agent」：确认 `.env` 有 `DEEPSEEK_API_KEY` 后重跑

### 单文件 / 调试（用户指定时）

```bash
.venv/bin/python3.14 -m pytest server/api/categories_test.py -v
.venv/bin/python3.14 -m pytest server/api/categories_test.py::test_get_category -v
```

仍须 API 已启动（步骤 1–2）。

---

## 反模式

- 不要用 `TestClient(app)`
- 不要封装 `assert_status_200()` 等 helper
- 不要为同一 `server/api/{entity}.py` 拆多个 `*_test.py`（如 `transactions_import_test.py`）
- 不要在测试里启动 uvicorn（API 由 Agent / 开发者手动起 `main.py`）
- 不要用硬编码 id（用 fixture 或 POST 创建）
- 不要放回 `server/test/`（已废弃）
- **不要** `unittest.mock`、`@patch`、mock LLM / mock DB（缺外部依赖时用 `pytest.skip`，见 `require_llm`）
- 只输出命令不执行；API 未起就把 skip 当通过
- 用 `uvicorn server.app:app` 绕过 `main.py`（会跳过 lifespan 迁移）

## 参考

- 环境搭建：[local-dev](../local-dev/SKILL.md)
