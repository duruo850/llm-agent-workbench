---
name: http-integration-test
description: 在 server/test 编写真实 HTTP 集成测试 SOP
---

# http-integration-test — HTTP 集成测试

## 何时触发

- 新增/修改 API 需要测试
- 用户要求「写测试」「加 test_*.py」

## 前置条件

- 已读 [Rules/testing.md](../../Rules/testing.md)
- API 已启动：`python server/main.py`

## 步骤清单

- [ ] 1. 确认 `server/test/conftest.py` fixture 可用（`http_client`、`category` 等）
- [ ] 2. 新建 `server/test/test_{entity}.py`（每表一文件）
- [ ] 3. 实现五用例：create / get / list / update / delete
- [ ] 4. 使用 `response.raise_for_status()` + 标准 `assert`
- [ ] 5. PATCH 后用 GET 验证（PATCH 可能空 body）
- [ ] 6. 列表断言 FastCRUD 格式：`assert "data" in body`
- [ ] 7. 自定义 API 断言返回形状（如 `list` 而非 `{data: ...}`）
- [ ] 8. 运行 `pytest server/test/test_{entity}.py -v`

## 文件清单

| 路径 | 操作 |
|------|------|
| `server/test/conftest.py` | 按需扩展 fixture |
| `server/test/test_{entity}.py` | 新建 |
| `pytest.ini` | 通常无需改 |

## 验收

```bash
# 终端 1
python server/main.py

# 终端 2
pytest server/test/test_category.py -v
pytest server/test -v
```

## 模板

参考 [`server/test/test_category.py`](../../../server/test/test_category.py)：

```python
def test_create_category(http_client: httpx.Client, unique_suffix: str) -> None:
    response = http_client.post("/categories", json={"name": f"新建-{unique_suffix}"})
    response.raise_for_status()
    body = response.json()
    assert body["name"] == ...
    http_client.delete(f"/categories/{body['id']}")
```

## 反模式

- 不要用 `TestClient(app)`
- 不要封装 `assert_status_200()` 等 helper
- 不要在测试里启动 uvicorn（session 级 API 由开发者手动起）
- 不要用硬编码 id（用 fixture 或 POST 创建）
