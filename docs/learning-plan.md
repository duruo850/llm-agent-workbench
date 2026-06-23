# LangChain / LangGraph / LlamaIndex 2 周学习计划

## 一、三个框架的关系和选择

**一句话关系：** LangChain 是基础库，LangGraph 是它的状态机/工作流增强，LlamaIndex 专注数据索引检索。它们可以也应该结合学习，但不要同时开始。

```
LangChain (基础组件) ──→ LangGraph (复杂 Agent 工作流)
    ↓ 互补
LlamaIndex (RAG/数据检索)
```

**你的最优路径：** 第 1 周聚焦 LangChain + LangGraph，第 2 周加入 LlamaIndex。三个框架共享 LLM 调用、向量存储等基础概念，一起学反而互相促进。

---

## 二、2 周详细学习计划

### 第 1 周：LangChain + LangGraph 核心链路

#### Day 1-2：LangChain 基础概念

理解三个核心抽象，直接看官方教程动手写。

**必学内容：**

| 抽象 | 说明 |
|------|------|
| Model | LLM 调用封装（以 OpenAI 兼容接口为例） |
| Prompt Template | 提示词模板化 |
| Chain | 串联多个步骤 |

**官方文档入口：**

- LangChain 快速入门：https://python.langchain.com/docs/introduction/
- 核心概念教程：https://python.langchain.com/docs/concepts/
- 快速开始 notebook：https://python.langchain.com/docs/tutorials/

**Day 1 动手任务：** 用 LangChain 写一个简单的 RAG 问答链，跑通整个流程。

```python
# 你的第一个 LangChain 程序
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o-mini")  # 或任何兼容接口
prompt = ChatPromptTemplate.from_template("用专业简洁的语言解释：{topic}")
chain = prompt | llm

result = chain.invoke({"topic": "Transformer 注意力机制"})
print(result.content)
```

#### Day 3-4：LangGraph 核心——把 Chain 变成 Agent

**关键认知转变：** LangGraph 的核心是**有状态的图**。Agent 不是线性的链，而是一个循环：思考 → 行动 → 观察 → 再思考。

**必学概念：**

| 概念 | 说明 |
|------|------|
| StateGraph | 状态图定义 |
| Node | 执行单元（调用 LLM、工具等） |
| Edge | 节点间的流转，包含条件边 |
| 循环控制 | Agent 的思考-行动循环 |

**官方文档入口：**

- LangGraph 快速入门：https://langchain-ai.github.io/langgraph/tutorials/introduction/
- 核心概念：https://langchain-ai.github.io/langgraph/concepts/low_level/
- Agent 教程（必做）：https://langchain-ai.github.io/langgraph/tutorials/introduction/#part-3-building-an-agent

**Day 3-4 动手任务：** 实现一个带搜索工具的 Agent。

```python
# Agent 的核心循环在 LangGraph 中长这样
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_community.tools.tavily_search import TavilySearchResults

# 1. 定义工具
tool = TavilySearchResults(max_results=1)
tools = [tool]

# 2. 绑定工具到模型
model_with_tools = llm.bind_tools(tools)

# 3. 定义图
def call_model(state: MessagesState):
    return {"messages": [model_with_tools.invoke(state["messages"])]}

graph = StateGraph(MessagesState)
graph.add_node("agent", call_model)
graph.add_node("tools", ToolNode(tools))
graph.add_edge(START, "agent")
graph.add_conditional_edges(
    "agent",
    lambda x: "tools" if x["messages"][-1].tool_calls else END,
)
graph.add_edge("tools", "agent")
```

#### Day 5-6：LlamaIndex 数据检索

**LlamaIndex 的核心价值：** 把各类数据（文档、数据库、API）索引化，让 Agent 高效检索。

**必学内容：**

| 概念 | 说明 |
|------|------|
| Document 和 Node | 文档加载和分块 |
| VectorStoreIndex | 向量索引 |
| QueryEngine | 检索问答 |

**官方文档入口：**

- LlamaIndex 介绍：https://docs.llamaindex.ai/en/stable/
- 入门教程：https://docs.llamaindex.ai/en/stable/getting_started/starter_tutorial/
- RAG 教程：https://docs.llamaindex.ai/en/stable/understanding/rag/

**Day 5-6 动手任务：** 把 LlamaIndex 检索能力作为 LangGraph Agent 的一个工具。

```python
# LlamaIndex 结合 LangGraph 的关键模式
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

# 1. 用 LlamaIndex 建立知识库
documents = SimpleDirectoryReader("./docs").load_data()
index = VectorStoreIndex.from_documents(documents)
query_engine = index.as_query_engine()

# 2. 封装成 LangChain 工具供 Agent 使用
from langchain_core.tools import tool

@tool
def query_knowledge_base(question: str) -> str:
    """搜索内部知识库获取信息"""
    return str(query_engine.query(question))
```

#### Day 7：三个框架联合调试

把 Day 6 的 Agent 完善，让搜索工具和知识库工具协同工作。重点调试：

- 工具选择是否合理
- 循环是否正常终止
- 错误处理

**关键调试文档：**

- LangGraph 调试：https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/breakpoints/
- Tracing 可视化：https://docs.smith.langchain.com/

---

### 第 2 周：进阶功能 + 面试项目

#### Day 8-9：Advanced 功能

| 主题 | 说明 | 教程 |
|------|------|------|
| 人机交互 | Agent 在执行关键操作前请求人工确认 | https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/breakpoints/ |
| 长期记忆 | 跨会话保持用户信息 | https://langchain-ai.github.io/langgraph/concepts/persistence/ |
| 并行执行 | 多个工具同时调用提升效率 | https://langchain-ai.github.io/langgraph/concepts/low_level/#send |

#### Day 10-14：面试级开源项目

**项目选题建议：**「智能文档分析 Agent」——结合三个框架的典型场景。

**核心功能：**

1. 用户上传多格式文档（PDF / 网页 / 数据库）
2. Agent 自动分析文档，提取关键信息
3. 支持追问、对比、总结
4. 复杂的分析流程（先提取 → 再对比 → 生成报告）

**技术栈：**

- **LlamaIndex**：文档加载和索引
- **LangChain**：工具封装和 Prompt 管理
- **LangGraph**：复杂多步骤分析流程编排
- **FastAPI**：接口封装
- 流式输出支持

**项目结构建议：**

```
doc-analysis-agent/
├── agent/
│   ├── graph.py          # LangGraph 工作流定义
│   ├── tools.py          # 工具封装（搜索/计算/API）
│   └── prompts.py        # Prompt 模板
├── indexer/
│   └── llama_indexer.py  # LlamaIndex 文档索引
├── api/
│   └── server.py         # FastAPI 接口
├── tests/
├── README.md             # 详细的项目说明
└── requirements.txt
```

---

## 三、面试准备策略

### 面试官会关注什么

| 维度 | 要点 |
|------|------|
| 理解深度 | 不只调 API，要能解释 Agent 的思考-行动循环原理 |
| 架构能力 | 为什么选择这个图结构，节点如何拆分 |
| 工程实践 | 错误处理、流式输出、评估方法 |

### README 中必须体现的亮点

```markdown
## 技术架构
- 架构图和设计决策说明
- 为什么用 LangGraph 处理复杂流程
- LlamaIndex 的索引策略选择

## 核心挑战
- Agent 循环的终止条件设计
- 多工具协作的上下文管理
- 流式输出的实现方案

## 评估结果
- 工具选择的准确率
- 响应延迟的优化措施
```

### 面试常见问题准备

**「Agent 和传统链式调用有什么区别？」**

→ 准备阐述：自主决策循环 vs 预定义流程

**「如何处理 Agent 的幻觉问题？」**

→ 回答方向：工具结果强制引用、事实性验证工具、置信度检查

**「LangGraph 的状态管理怎么做的？」**

→ 回答：类型化的 State、checkpoint 持久化、支持回退

---

## 四、学习资源优先级

按依赖关系排序：

| 顺序 | 资源 | 时间 | 目标 |
|------|------|------|------|
| 1 | https://python.langchain.com/docs/introduction/ | 30 分钟 | 建立全局认知 |
| 2 | https://python.langchain.com/docs/tutorials/ | 2 天 | 边看边写，跟完 RAG 和 Agent 两个 tutorial |
| 3 | https://langchain-ai.github.io/langgraph/tutorials/introduction/ | 2 天 | 深入 Agent，完全掌握 Agent 构建 |
| 4 | https://docs.llamaindex.ai/en/stable/getting_started/starter_tutorial/ | 1 天 | LlamaIndex 补充，为项目增加检索能力 |
| 5 | 项目实战 | 4-5 天 | 把上面学到的整合进 GitHub 项目 |

---

## 结语

你的服务端经验会让这个过程更顺畅——Agent 本质是状态机、API 编排、异步处理这些你本来就熟悉的概念。重点是理解 LLM 的不确定性带来的设计变化。两周后你不仅能用，还能在面试中讲清楚设计权衡。
