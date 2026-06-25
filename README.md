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

详细增量计划见 [docs/learning-plan.md](docs/learning-plan.md)。

**第 1 周**
- [x] M0 LangChain 解析记账意图
- [x] M1 FastAPI + PostgreSQL
- [ ] M2-M4 Function Calling + LangGraph Agent + 聊天前端

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
- **存储**: MySQL + Chroma（向量）
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

# 图片入账（Ollama 本地视觉模型，见 examples/README.md）
./examples/setup-ollama.sh
python examples/01_image_ollama_chain.py
```

图片入账详见 [examples/README.md](examples/README.md)。

### M1 服务端（PostgreSQL）

```bash
docker compose -f server/docker-compose.yml up -d
alembic -c server/alembic.ini upgrade head
uvicorn server.main:app --reload --port 8000
curl http://localhost:8000/health
```

详见 [server/README.md](server/README.md)。

## 📖 项目结构

```
llm-agent-workbench/
├── server/                  # FastAPI + PostgreSQL
├── agent/                   # LangGraph Agent + Tools + Skills
├── indexer/                 # LlamaIndex RAG + Embeddings
├── frontend/                # 聊天 + 仪表盘
├── src/common/              # LLM 平台抽象 + DeepSeek / Ollama 封装
├── examples/                # 各阶段独立 demo
├── docs/                    # 学习计划
└── tests/
```
