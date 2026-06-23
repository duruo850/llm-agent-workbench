# 🤖 LLM Agent Workbench

> 基于 LangChain、LangGraph、LlamaIndex 的 AI Agent 开发实践工作台

## 🎯 项目目标

- 系统学习三大框架的核心概念和最佳实践
- 构建可复用的 Agent 开发模板
- 积累面试级项目经验

## 📚 学习路线

详细计划见 [docs/learning-plan.md](docs/learning-plan.md)。

- [ ] Phase 1: LangChain 基础 (Chain、Prompt、Model)
- [ ] Phase 2: LangGraph Agent (状态图、工具调用、循环控制)
- [ ] Phase 3: LlamaIndex RAG (文档索引、检索增强)
- [ ] Phase 4: 综合实战 (文档分析 Agent)

## 🛠️ 技术栈

- **框架**: LangChain + LangGraph + LlamaIndex
- **LLM**: DeepSeek（OpenAI 兼容接口）
- **语言**: Python 3.11+
- **工具**: Tavily Search, SQL, Code Interpreter

## 🚀 快速开始

```bash
pip install -r requirements.txt
# 配置 .env 文件
cp .env.example .env
# 填入 DEEPSEEK_API_KEY 后运行示例
python examples/01_basic_chain.py
```

## 📖 项目结构

```
llm-agent-workbench/
├── src/
│   └── common/              # DeepSeek API 公共封装
│       ├── deepseek_client.py   # OpenAI SDK 客户端
│       └── deepseek_adapter.py  # 模型 Adapter
├── examples/                # 渐进式示例代码
├── docs/                    # 学习笔记
└── tests/                   # 单元测试
```
