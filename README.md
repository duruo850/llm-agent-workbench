# 🤖 BillMind — 个人记账助理 Agent

> 边学 LangChain / LangGraph / LlamaIndex，边做全栈 AI Agent 实战项目

## 🎯 项目目标

- 系统学习 AI 应用开发全栈技术（Agent、RAG、Embeddings、Function Calling、Fine-tuning、Skills）
- 实战交付「个人记账助理 Agent」—— 自然语言记账、查账、分析、文件导入、财务问答
- 积累可演示、可写进简历的面试级项目
- 用自然语言记账、查账、分析个人财务
- 系统掌握 AI 应用全链路：Chain → Agent → RAG → Embeddings → Skills → Fine-tuning
- 交付可演示的后端 + 前端 + Agent 面试级项目

## 📚 学习路线

详细增量计划见 [docs/learning-plan.md](docs/learning-plan.md)。各主题本质讲解见 [docs/knowledge/](docs/knowledge/README.md)。

**第 1 周**
- [x] M0 LangChain 解析记账意图
- [x] M1 FastAPI + PostgreSQL
- [x] M2 Function Calling 记一笔 / 查账
- [ ] M3-M4 LangGraph Agent + 聊天前端

**第 2 周**
- [ ] M5-M6 文件导入 + RAG 知识库
- [ ] M7-M8 Embeddings/RAG 语义搜账 + 月报工作流

**第 3 周**
- [ ] M9-M11 Memory / HITL / Skills
- [ ] M12-M13 Fine-tuning 实验 + 仪表盘

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
