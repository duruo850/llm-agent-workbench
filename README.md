# 🤖 BillMind — 个人记账助理 Agent

> 边学 LangChain / LangGraph / LlamaIndex，边做全栈 AI Agent 实战项目

## 🎯 项目目标

- 系统学习 AI 应用开发全栈技术（Agent、RAG、Embeddings、Function Calling、Fine-tuning、Skills）
- 实战交付「个人记账助理 Agent」—— 自然语言记账、查账、分析、文件导入、财务问答
- 积累可演示、可写进简历的面试级项目
- 用自然语言记账、查账、分析个人财务
- 系统掌握 AI 应用全链路：Chain → Agent → RAG → Embeddings → Skills → Fine-tuning
- 交付可演示的后端 + 前端 + Agent 面试级项目

## 🛠️ 技术栈

- **Agent**: LangChain + LangGraph + Function Calling
- **RAG**: LlamaIndex + Chroma + Embeddings
- **LLM**: DeepSeek（云端文本）+ Ollama（本地视觉，OpenAI 兼容接口）
- **存储**: PostgreSQL + Chroma（向量，M6+）
- **后端**: FastAPI（SSE 流式）
- **前端**: React + Vite
- **进阶**: Embeddings、Fine-tuning、Agent Skills、LangSmith

## 🚀 快速开始

```bash
pip install -r requirements.txt
# 配置 .env 文件
cp .env.example .env
# 填入 DEEPSEEK_API_KEY 后运行 M0 文本入账示例
python examples/00_hello_chain.py

# 图片入账（Ollama 本地视觉模型，见 examples/01_image_ollama_chain/README.md）
./examples/01_image_ollama_chain/setup-ollama.sh
python examples/01_image_ollama_chain/01_image_ollama_chain.py
```

图片入账详见 [examples/01_image_ollama_chain/README.md](examples/01_image_ollama_chain/README.md)。

### M1 服务端（PostgreSQL）

```bash
docker compose up -d
python server/main.py
curl http://localhost:8000/health
```

启动时自动执行 Alembic 迁移。详见 [server/README.md](server/README.md) 与 [.harness/Skills/local-dev/SKILL.md](.harness/Skills/local-dev/SKILL.md)。

### M2 Agent（Function Calling）

```bash
docker compose up -d

# CLI（直连 PostgreSQL，无需单独起 API）
.venv/bin/python3.14 examples/02_function_calling_agent.py
.venv/bin/python3.14 examples/02_function_calling_agent.py --repl

# HTTP（Server 注入 db session）
python server/main.py
curl -X POST http://127.0.0.1:8000/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"刚才地铁花了6块，交通"}'
```

## 📖 项目结构

```
llm-agent-workbench/
├── server/                  # FastAPI + PostgreSQL
├── agent/                   # LangGraph Agent + Tools + Skills
├── indexer/                 # LlamaIndex RAG + Embeddings
├── web/                     # 聊天 + 仪表盘
├── common/                  # LLM 平台抽象 + DeepSeek / Ollama 封装
├── examples/                # 各阶段独立 demo
├── docs/                    # 学习计划 + knowledge/ 知识点深度文档
├── .harness/                # Agent 编码规范（Rules / Skills / Wiki / Changes）
└── server/api/              # HTTP 路由 + *_test.py 集成测试
```

Agent 实现功能前请读 [AGENTS.md](AGENTS.md) 与 [.harness/](.harness/)。里程碑交付单见 [.harness/Changes/](.harness/Changes/)。

## 💬 会话与 Loop 数据模型（M9 / M10）

一次用户聊天在库里的层级关系：

```
conversation（1 次会话，thread_id）
  └─ turn × N（每轮 POST /agent/chat，turn_id）
       ├─ chat_messages × 2（user + assistant）
       ├─ agent_loop_runs × 1（LoopRunResult 汇总：步数、token、input/output_message）
       └─ agent_loop_steps × M（loop 内每步 LLM / 工具指标）
```

| 概念 | 表 / 字段 | 说明 |
|------|-----------|------|
| **conversation** | `conversations` | 按 `account_id` + `thread_id` 标识整场对话 |
| **turn** | `agent_loop_runs.turn_id` | 单次 `/agent/chat`；1 turn = 2 条 `chat_messages` |
| **loop 汇总** | `agent_loop_runs` | 存 `LoopRunResult`（`total_steps`、`total_tokens`、`input_message`、`output_message` 等） |
| **loop 单步** | `agent_loop_steps` | ReAct 循环内每一步的 token / 工具名 |

跨轮记忆：`thread_id` → LangGraph checkpointer；业务历史 → `chat_messages`。
