---
name: http-integration-test
description: 在 server/api 编写真实 HTTP 集成测试 SOP（与路由同目录 *_test.py）
---

# http-integration-test — HTTP 集成测试

## 何时触发

- 新增/修改 API 需要测试
- 用户要求「写测试」「加 *_test.py」

## 前置条件

- 已读 [Rules/testing.md](../../Rules/testing.md)
- API 已启动：`python server/main.py`

## 命名与位置

- 测试与 API **同目录**：`server/api/{feature}_test.py`
- 示例：`categories.py` → `categories_test.py`，`agent.py` → `agent_test.py`
- 共用 fixture：`server/api/conftest.py`

## 步骤清单

- [ ] 1. 确认 `server/api/conftest.py` fixture 可用（`http_client`、`category` 等）
- [ ] 2. 新建 `server/api/{entities}_test.py`（每路由模块一文件）
- [ ] 3. 实现五用例：create / get / list / update / delete（健康检查等例外见 `health_test.py`）
- [ ] 4. 使用 `response.raise_for_status()` + 标准 `assert`
- [ ] 5. PATCH 后用 GET 验证（PATCH 可能空 body）
- [ ] 6. 分页列表断言：`assert "data" in body`
- [ ] 7. 自定义 API 断言返回形状（如 Transaction 按月列表为 `list`）
- [ ] 8. 运行 `pytest server/api/{entities}_test.py -v`

## 文件清单

| 路径 | 操作 |
|------|------|
| `server/api/conftest.py` | 按需扩展 fixture |
| `server/api/{feature}_test.py` | 新建 |
| `pytest.ini` | `testpaths = server/api`，`python_files = *_test.py` |

## 验收

```bash
# 终端 1
python server/main.py

# 终端 2
pytest server/api/categories_test.py -v
pytest server/api -v
```

## 模板

参考 [`server/api/categories_test.py`](../../../server/api/categories_test.py)：

```python
def test_create_category(http_client: httpx.Client, unique_suffix: str) -> None:
    response = http_client.post("/categories", json={"name": f"新建-{unique_suffix}"})
    response.raise_for_status()
    body = response.json()
    assert body["name"] == ...
    http_client.delete(f"/categories/{body['id']}")
```

Agent 真实 LLM 参考 [`server/api/agent_test.py`](../../../server/api/agent_test.py)（无 mock，依赖 `DEEPSEEK_API_KEY`）。

## 反模式

- 不要用 `TestClient(app)`
- 不要封装 `assert_status_200()` 等 helper
- 不要在测试里启动 uvicorn（session 级 API 由开发者手动起）
- 不要用硬编码 id（用 fixture 或 POST 创建）
- 不要放回 `server/test/`（已废弃）
- **不要** `unittest.mock`、`@patch`、mock LLM / mock DB（缺外部依赖时用 `pytest.skip`，见 `require_llm`）
