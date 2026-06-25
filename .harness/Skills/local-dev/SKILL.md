---
name: local-dev
description: 本地开发 SOP：docker、main、pytest、F5 调试
---

# local-dev — 本地开发

## 何时触发

- 首次搭建环境
- 用户问「怎么跑 server」「怎么调试」

## 前置条件

- Python 3.11+（项目用 `.venv/bin/python3.14`）
- Docker Desktop 或兼容 runtime

## 步骤清单

- [ ] 1. `pip install -r requirements.txt`（在 `.venv` 内）
- [ ] 2. `cp .env.example .env`，填入 `DEEPSEEK_API_KEY`（M0）与 `DATABASE_URL`（M1）
- [ ] 3. `docker compose up -d` — 启动 PostgreSQL（根目录 compose）
- [ ] 4. `python server/main.py` — 自动迁移 + 启动 API `:8000`
- [ ] 5. `curl http://127.0.0.1:8000/health` 验收
- [ ] 6. 测试：`pytest server/test -v`（须 API 已启动）
- [ ] 7. F5 调试：选 `.vscode/launch.json` 配置

## 文件清单

| 路径 | 说明 |
|------|------|
| `docker-compose.yml` | PostgreSQL 16 |
| `.env` | 环境变量 |
| `server/main.py` | API 入口 |
| `.vscode/launch.json` | 调试配置 |
| `pytest.ini` | 测试配置 |

## Launch 配置

| 名称 | 用途 |
|------|------|
| BillMind API (server/main.py) | 断点调试 API（reload=False） |
| BillMind API (uvicorn reload) | 热重载开发 |
| Debug pytest (current file) | 调试当前测试文件 |
| Debug pytest (test_budget.py) | 示例预算测试 |

## M0 示例

```bash
python examples/00_hello_chain.py
./examples/01_image_ollama_chain/setup-ollama.sh
python examples/01_image_ollama_chain/01_image_ollama_chain.py
```

## 验收

```bash
curl http://127.0.0.1:8000/health
pytest server/test/test_health.py -v
```

## 反模式

- 不要用 `server/docker-compose.yml`（路径已过时）
- 不要 `uvicorn` 启动却不经过 `main.py` lifespan（会跳过自动迁移）
- 不要在未起 API 时期望 pytest 全绿（会 skip）

## 常见问题

| 问题 | 处理 |
|------|------|
| 数据库连接失败 | `docker compose ps`，确认 5432 端口 |
| pytest skip API 未启动 | 另开终端 `python server/main.py` |
| 迁移未应用 | 看 main 启动日志；或手动 `alembic -c server/alembic.ini upgrade head` |
