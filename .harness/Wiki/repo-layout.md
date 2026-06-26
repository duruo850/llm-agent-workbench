# 目录布局 — 实际 vs learning-plan

`docs/learning-plan.md` 描述**目标态**；本页描述**仓库当前实际结构**。

## 对照表

| learning-plan | 实际 | 说明 |
|---------------|------|------|
| `backend/` | [`server/`](../../server/) | FastAPI + PostgreSQL |
| `src/common/` | [`common/`](../../common/) | env + LLM 封装 |
| MySQL | PostgreSQL + `asyncpg` | `DATABASE_URL` |
| `backend/schemas/` | `server/model/request/` + `response/` | 请求/响应分离 |
| `TransactionTable` | `Transaction` | SQLModel `table=True` |
| `server/docker-compose.yml` | 根 [`docker-compose.yml`](../../docker-compose.yml) | PostgreSQL 16 |
| 手动 alembic | 启动 `main` 自动迁移 | CLI 仍可用 |
| `tests/` | [`server/api/*_test.py`](../../server/api/) | HTTP 集成测试（与路由同目录） |
| `agent/` | [`agent/`](../../agent/) | M2 for 循环 Agent |
| `graph/` | [`graph/`](../../graph/) | M4 LangGraph Agent |
| `web/` | [`web/`](../../web/) | M3 聊天页 |
| `indexer/` | 未创建 | M6+ |

## 当前根目录

```
llm-agent-workbench/
├── .harness/           # Agent 规范（本目录）
├── AGENTS.md           # Agent 入口
├── server/             # M1 FastAPI + PostgreSQL
├── common/             # 共享 env + LLM
├── utils/              # 通用纯函数（date_range、map_by_name 等）
├── agent/              # M2 Agent（for 循环 + function_calling）
├── graph/              # M4 LangGraph Agent（与 agent/ 并列对比）
├── examples/           # M0 LangChain demo
├── web/                # M3 React 聊天页
├── docs/               # learning-plan 课表
├── docker-compose.yml  # PostgreSQL
├── .env.example
├── pytest.ini
└── requirements.txt
```

## 历史/冗余目录

仓库中可能存在 `backend/`、`src/` 等历史副本，**以 `server/` + `common/` 为准**。新代码不要写入 `backend/` 或 `src/backend/`。

## server/ 内部

```
server/
├── main.py
├── routers.py      # 路由注册
├── api/            # HTTP 编排 + *_test.py 集成测试
├── service/        # 业务 Service + enter.py
├── db/             # session + migrate
├── model/
│   ├── category.py / budget.py / transaction.py
│   ├── request/
│   └── response/
└── alembic/
```

## examples/ 结构

```
examples/
├── 00_hello_chain.py              # M0 文本入账
└── 01_image_ollama_chain/         # M0+ Ollama 视觉
    ├── 01_image_ollama_chain.py
    ├── docker-compose.yml         # Ollama 服务
    └── setup-ollama.sh
```

## 配置与环境

- 环境变量：根 `.env`（模板 `.env.example`）
- 加载：[`common/env.py`](../../common/env.py)
- Python：`.venv/bin/python3.14`

## 相关

- [architecture.md](architecture.md)
- [server.md](server.md)
