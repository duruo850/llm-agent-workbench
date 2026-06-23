# 个人记账助理 Agent — 边学边做实战计划

> **项目代号：BillMind** — 用自然语言记账、查账、分析的个人财务助理（后端 + 前端 + Agent 全栈）

---

## 一、项目愿景与增量路线

### 1.1 一句话定位

用户说「刚才 Starbucks 花了 38」→ Agent 解析意图 → 调用 MySQL 工具写入 → 返回确认；用户问「本月餐饮超预算了吗」→ Agent 查库 + RAG 查记账规则 → 生成分析报告。

### 1.2 三个框架的关系（学习顺序不变）

**LangChain** 是基础库，**LangGraph** 是它的状态机/工作流增强，**LlamaIndex** 专注数据索引检索。边做 BillMind 边学，按增量里程碑推进，不要一次堆全部功能。

```
LangChain (Chain / Tool / Prompt)
    ↓
LangGraph (记账 Agent 工作流：解析→确认→入库→报告)
    ↓ 互补
LlamaIndex (RAG：记账规则 / 理财知识 / 用户备注)
    ↓
Embeddings + Vector DB (语义搜历史账单)
    ↓
Fine-tuning / Skills (分类微调 / 可插拔技能模块)
```

### 1.3 增量里程碑总览

每完成一个里程碑，项目都是**可运行、可演示**的状态：

| 里程碑 | 交付物 | 新增能力 |
|--------|--------|----------|
| **M0** | `examples/00_hello_chain.py` | LangChain + DeepSeek 跑通 |
| **M1** | `backend/` + MySQL schema | 交易 CRUD API |
| **M2** | `agent/tools/db_tools.py` | Function Calling 记一笔 / 查账 |
| **M3** | `frontend/` 聊天页 | 流式对话 UI |
| **M4** | `agent/graph.py` | LangGraph 多步 Agent |
| **M5** | `agent/tools/file_tools.py` | CSV / 账单文件导入 |
| **M6** | `indexer/` + RAG 工具 | 记账规则 / 知识库问答 |
| **M7** | `indexer/embeddings.py` | 语义搜历史消费 |
| **M8** | 月报 / 预算分析图 | LangGraph 复杂工作流 |
| **M9** | Checkpoint + HITL | 长期记忆 + 大额人工确认 |
| **M10** | Eval + LangSmith | 工具选择准确率 / Tracing |
| **M11** | `skills/` 模块 | 可插拔 Skills（报税 / 投资等） |
| **M12** | Fine-tuning 实验 | 消费分类 LoRA（可选进阶） |
| **M13** | 前端仪表盘 | 图表 + 完整产品体验 |

### 1.4 目标项目结构（随里程碑逐步创建）

```
billmind/
├── backend/
│   ├── api/                 # FastAPI 路由
│   ├── db/                  # MySQL models / migrations
│   └── schemas/             # Pydantic 模型
├── agent/
│   ├── graph.py             # LangGraph 工作流
│   ├── tools/
│   │   ├── db_tools.py      # MySQL Function Calling
│   │   ├── file_tools.py    # CSV / PDF 导入
│   │   └── rag_tools.py     # 知识库检索
│   ├── prompts.py
│   └── skills/              # 可插拔 Skills
│       ├── budget_skill.py
│       └── tax_skill.py
├── indexer/
│   ├── llama_indexer.py     # LlamaIndex 文档索引
│   └── embeddings.py        # 交易向量索引
├── frontend/
│   ├── src/                 # React / Vue 聊天 + 仪表盘
│   └── ...
├── data/
│   ├── knowledge/           # RAG 知识库（记账规则、理财笔记）
│   └── imports/             # 用户上传的账单文件
├── eval/                    # Agent 评测脚本
├── examples/                # 各阶段独立小 demo
├── src/common/              # DeepSeek 公共封装（已有）
└── tests/
```

---

## 二、技术栈全景

| 类别 | 技术 | 在 BillMind 中的用途 |
|------|------|----------------------|
| LLM | DeepSeek（OpenAI 兼容） | 对话、意图解析、报告生成 |
| 编排 | LangChain | Prompt、Chain、Tool 封装 |
| Agent | LangGraph | 记账 / 分析多步工作流 |
| RAG | LlamaIndex | 记账规则、理财知识检索 |
| 向量 | Embeddings + Chroma | 历史账单语义搜索 |
| 工具 | Function Calling | MySQL CRUD、文件解析、计算 |
| 存储 | MySQL | 交易、分类、预算表 |
| 文件 | CSV / Excel / PDF | 银行流水、收据导入 |
| 后端 | FastAPI | REST + SSE 流式 |
| 前端 | React + Vite（或 Vue） | 聊天 + 仪表盘 |
| 观测 | LangSmith | Tracing、调试 |
| 评测 | 自建 Eval Harness | 工具选择 / 分类准确率 |
| 进阶 | Fine-tuning（LoRA） | 消费分类微调 |
| 扩展 | Agent Skills | 报税、投资等可插拔模块 |

---

## 三、3 周详细学习计划（边学边做）

> 官方文档链接全部保留；**实战任务**均指向 BillMind 增量交付。

---

### 第 1 周：LangChain 基础 + 后端骨架 + 第一个 Agent 工具

#### Day 1：LangChain 基础 + M0

**必学概念：**

| 抽象 | 说明 |
|------|------|
| Model | LLM 调用封装（DeepSeek OpenAI 兼容接口） |
| Prompt Template | 提示词模板化 |
| Chain | 串联多个步骤 |

**官方文档：**

- LangChain 快速入门：https://python.langchain.com/docs/introduction/
- 核心概念：https://python.langchain.com/docs/concepts/
- 快速开始 notebook：https://python.langchain.com/docs/tutorials/

**实战任务 → M0：** 用 LangChain + 项目已有 `src/common/deepseek_client.py` 写「自然语言解析记账意图」链。

```python
# examples/00_hello_chain.py — 解析「Starbucks 38 餐饮」
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.common.deepseek_client import BASE_URL, MODEL
import os

llm = ChatOpenAI(
    model=MODEL,
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=BASE_URL,
)
prompt = ChatPromptTemplate.from_template(
    "从用户输入中提取 JSON：amount, category, merchant, note。\n输入：{text}"
)
chain = prompt | llm
result = chain.invoke({"text": "刚才 Starbucks 花了 38，算餐饮"})
print(result.content)
```

**验收：** 输出结构化 JSON，能正确解析 3 条以上测试语句。

---

#### Day 2：FastAPI 后端 + M1

**必学概念：** REST API、Pydantic、SQLAlchemy / asyncmy、数据库迁移。

**官方文档：**

- FastAPI 教程：https://fastapi.tiangolo.com/tutorial/
- LangChain 与 FastAPI 集成：https://python.langchain.com/docs/langserve/

**实战任务 → M1：** 搭建 `backend/`，设计 MySQL 表并暴露 CRUD。

```sql
-- 核心表（Day 2 先建这 3 张）
transactions (id, amount, category, merchant, note, transacted_at, created_at)
categories   (id, name, budget_monthly)
budgets      (id, category_id, month, limit_amount)
```

**API 清单（先 REST，Day 3 再包成 Agent 工具）：**

- `POST /transactions` — 记一笔
- `GET /transactions?month=2025-06` — 按月查账
- `GET /summary/monthly` — 月度汇总

**验收：** Postman / curl 能完成增删改查。

---

#### Day 3-4：Function Calling + M2

**关键认知：** Agent 工具 = 带 schema 的函数；LLM 决定调哪个工具、传什么参数。

**必学概念：**

| 概念 | 说明 |
|------|------|
| `@tool` 装饰器 | LangChain 工具定义 |
| `bind_tools` | 模型绑定工具 |
| Structured Output | 强制 JSON 输出（解析失败时的兜底） |

**官方文档：**

- LangChain Tools：https://python.langchain.com/docs/concepts/tools/
- Function Calling 教程：https://python.langchain.com/docs/how_to/function_calling/

**实战任务 → M2：** 把 Day 2 的 API 封装为 Agent 工具。

```python
# agent/tools/db_tools.py
from langchain_core.tools import tool

@tool
def add_transaction(amount: float, category: str, merchant: str, note: str = "") -> str:
    """记一笔支出或收入。amount 为正数表示支出。"""
    ...

@tool
def query_transactions(month: str, category: str | None = None) -> str:
    """查询指定月份的交易记录，可选按分类过滤。month 格式 YYYY-MM。"""
    ...

@tool
def get_monthly_summary(month: str) -> str:
    """获取指定月份的分类汇总与总支出。"""
    ...
```

**验收：** 命令行 Agent 能完成「记一笔」「查本月餐饮花了多少」。

---

#### Day 5-6：LangGraph Agent + M4

**关键认知转变：** LangGraph 的核心是**有状态的图**。记账不是一次 LLM 调用，而是：解析意图 →（可选）确认 → 执行工具 → 生成回复。

**必学概念：**

| 概念 | 说明 |
|------|------|
| StateGraph | 状态图定义 |
| Node | 执行单元（LLM、工具） |
| Edge / 条件边 | 是否继续调工具 |
| 循环控制 | 思考 → 行动 → 观察 |

**官方文档：**

- LangGraph 快速入门：https://langchain-ai.github.io/langgraph/tutorials/introduction/
- 核心概念：https://langchain-ai.github.io/langgraph/concepts/low_level/
- Agent 教程（必做）：https://langchain-ai.github.io/langgraph/tutorials/introduction/#part-3-building-an-agent

**实战任务 → M4：** 实现 BillMind 核心 Agent 图。

```python
# agent/graph.py — 记账 Agent 核心循环
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

# tools = [add_transaction, query_transactions, get_monthly_summary]
# graph: START → agent → (有 tool_calls?) → tools → agent → END
```

**验收：** 支持多轮对话（「刚才那笔改成分类交通」），工具循环正常终止。

---

#### Day 7：前端聊天页 + M3

**必学概念：** SSE 流式、前后端分离、Agent API 封装。

**官方文档：**

- LangGraph Streaming：https://langchain-ai.github.io/langgraph/how-tos/streaming/
- FastAPI StreamingResponse：https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse

**实战任务 → M3：** 最小聊天前端 + 流式输出。

- `POST /chat` — 接收用户消息，SSE 流式返回 Agent 回复
- 前端：输入框 + 消息列表 + 流式打字效果
- 可选：侧边栏展示最近 5 笔交易（调 REST API）

**验收：** 浏览器里用自然语言完成记账和查账。

---

### 第 2 周：RAG + 文件导入 + Embeddings + 复杂工作流

#### Day 8-9：LlamaIndex RAG + M6

**LlamaIndex 核心价值：** 把记账规则、理财笔记、用户上传说明文档索引化，Agent 查规则时有据可依。

**必学概念：**

| 概念 | 说明 |
|------|------|
| Document / Node | 文档加载与分块 |
| VectorStoreIndex | 向量索引 |
| QueryEngine | 检索问答 |

**官方文档：**

- LlamaIndex 介绍：https://docs.llamaindex.ai/en/stable/
- 入门教程：https://docs.llamaindex.ai/en/stable/getting_started/starter_tutorial/
- RAG 教程：https://docs.llamaindex.ai/en/stable/understanding/rag/

**实战任务 → M6：**

1. 在 `data/knowledge/` 放入记账规则（如「餐饮预算 2000/月」「报销需保留发票」）
2. `indexer/llama_indexer.py` 建立索引
3. 封装 `query_accounting_rules` 工具供 Agent 调用

```python
# agent/tools/rag_tools.py
@tool
def query_accounting_rules(question: str) -> str:
    """查询个人记账规则、预算政策、理财知识库。"""
    return str(query_engine.query(question))
```

**验收：** 问「餐饮预算是多少」能 RAG 命中知识库，而非 LLM 幻觉。

---

#### Day 10：文件导入工具 + M5

**必学概念：** 文档 Loader、结构化解析、工具链组合。

**官方文档：**

- LangChain Document Loaders：https://python.langchain.com/docs/concepts/document_loaders/
- LlamaIndex 文件读取：https://docs.llamaindex.ai/en/stable/module_guides/loading/

**实战任务 → M5：** 支持 CSV / Excel 银行流水导入。

```python
@tool
def import_bank_statement(file_path: str) -> str:
    """解析 CSV/Excel 银行流水，批量写入 transactions 表。返回导入条数与摘要。"""
    ...
```

**进阶（可选）：** PDF 收据 OCR（`unstructured` / `pytesseract`）。

**验收：** 上传一份 CSV，Agent 批量导入并汇报「共导入 47 笔，餐饮 12 笔合计 856 元」。

---

#### Day 11-12：Embeddings 语义检索 + M7

**必学概念：** Embedding 模型、向量相似度、Hybrid Search（关键词 + 语义）。

**官方文档：**

- LangChain Embeddings：https://python.langchain.com/docs/concepts/embedding_models/
- LlamaIndex Vector Store：https://docs.llamaindex.ai/en/stable/module_guides/storing/vector_stores/
- Chroma 文档：https://docs.trychroma.com/

**实战任务 → M7：** 历史交易语义搜索。

```python
@tool
def search_similar_transactions(query: str, top_k: int = 5) -> str:
    """语义搜索历史消费，如「上次买咖啡花了多少」「类似的出差住宿」。"""
    ...
```

**实现路径：** 每笔交易 embedding 存 Chroma；新交易写入时同步更新向量索引。

**验收：** 「上次在 Starbucks 花了多少」能命中历史记录，即使用户没说具体日期。

---

#### Day 13-14：复杂工作流 + M8

**必学概念：** 多节点图、子图、并行（Send API）。

**官方文档：**

- LangGraph Workflow 教程：https://langchain-ai.github.io/langgraph/tutorials/workflows/
- Send API（并行）：https://langchain-ai.github.io/langgraph/concepts/low_level/#send
- LangGraph 子图：https://langchain-ai.github.io/langgraph/concepts/subgraphs/

**实战任务 → M8：** 月度财务报告工作流。

```
用户：「生成本月财务报告」
  → 节点1: 拉取本月交易 (db_tools)
  → 节点2: 按分类汇总 (并行 Send)
  → 节点3: 对比预算 (db_tools + rag_tools)
  → 节点4: LLM 生成 Markdown 报告
  → 节点5: 返回前端渲染
```

**验收：** 一键生成含分类占比、预算对比、超支提醒的报告。

---

### 第 3 周：进阶 Agent 能力 + Skills + Fine-tuning + 产品化

#### Day 15-16：Memory + 人机确认 + M9

**官方文档：**

- LangGraph Persistence：https://langchain-ai.github.io/langgraph/concepts/persistence/
- Human-in-the-loop：https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/breakpoints/
- LangGraph Memory：https://langchain-ai.github.io/langgraph/concepts/memory/

**实战任务 → M9：**

| 能力 | BillMind 场景 |
|------|---------------|
| Checkpoint | 跨会话记住用户偏好（默认分类、常用商户） |
| HITL | 单笔超过 5000 元时暂停，前端弹确认再继续入库 |
| Thread ID | 前端每个对话窗口对应一个 thread |

**验收：** 刷新页面后 Agent 仍记得「我常用餐饮分类」；大额记账需点确认。

---

#### Day 17：Agent Skills 模块化 + M11

**必学概念：** Skills = 独立能力包（Prompt + Tools + 子图），按需挂载到主 Agent。

**参考：**

- LangGraph 多 Agent：https://langchain-ai.github.io/langgraph/concepts/multi_agent/
- Cursor Agent Skills 设计思路（本项目 `agent/skills/` 目录）

**实战任务 → M11：** 实现 2 个可插拔 Skills。

```
agent/skills/
├── budget_skill.py    # 预算分析专家：专用 prompt + 工具子集
└── tax_skill.py       # 报税助手：RAG 税规则 + 年度汇总工具
```

主 Agent 路由逻辑：用户意图匹配 → 加载对应 Skill 的子图或工具集。

**验收：** 「帮我看看要不要报税」自动路由到 tax_skill，不影响日常记账。

---

#### Day 18-19：评测 + 可观测性 + M10

**官方文档：**

- LangSmith 入门：https://docs.smith.langchain.com/
- LangGraph 调试：https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/breakpoints/
- LangChain Evaluation：https://python.langchain.com/docs/concepts/evaluation/

**实战任务 → M10：** 建立 BillMind Eval 集。

```python
# eval/test_cases.json — 示例
[
  {"input": "Starbucks 38 餐饮", "expected_tool": "add_transaction"},
  {"input": "本月餐饮花了多少", "expected_tool": "query_transactions"},
  {"input": "餐饮预算是多少", "expected_tool": "query_accounting_rules"}
]
```

**指标：** 工具选择准确率、结构化解析 F1、端到端延迟 P95。

**验收：** `python eval/run_eval.py` 输出报告；LangSmith 可看到完整 trace。

---

#### Day 20-21：Fine-tuning 进阶 + M12（可选）

**必学概念：** 数据准备、LoRA/QLoRA、分类任务微调 vs Prompt 方案对比。

**官方文档：**

- OpenAI Fine-tuning：https://platform.openai.com/docs/guides/fine-tuning
- Hugging Face PEFT / LoRA：https://huggingface.co/docs/peft
- DeepSeek Fine-tuning 指南（若官方提供）

**实战任务 → M12：** 消费分类 Fine-tuning 实验。

1. 从 MySQL 导出 `(merchant, note) → category` 训练集（≥500 条）
2. 训练 LoRA 分类头 或 微调小模型
3. 与 Prompt + Function Calling 方案做 A/B 对比

**验收：** README 记录：微调 vs Prompt 在测试集上的准确率、成本、延迟对比。**不强求部署**，理解权衡即可。

---

#### Day 22-23：前端仪表盘 + M13

**实战任务 → M13：** 完善前端产品体验。

| 页面 | 功能 |
|------|------|
| 聊天页 | 流式对话、工具调用过程可视化、HITL 确认弹窗 |
| 仪表盘 | 月度支出饼图、分类趋势折线、预算进度条 |
| 导入页 | 拖拽上传 CSV、导入进度与结果 |
| 设置页 | 分类管理、预算配置、知识库文档上传 |

**验收：** 完整 Demo 可录屏展示：记账 → 查账 → 导入 → 月报 → 预算预警。

---

#### Day 24-25：联调、文档、面试准备

见下方「第四节」。

---

## 四、联调检查清单（Day 7 / 14 / 25 各做一次）

- [ ] 工具选择是否合理（记账 vs 查账 vs 查规则）
- [ ] Agent 循环是否正常终止（max_iterations 兜底）
- [ ] MySQL 事务与幂等（重复导入 CSV 不重复写入）
- [ ] 流式输出中断恢复
- [ ] RAG 检索为空时的降级回复
- [ ] 错误处理：API Key 缺失、DB 连接失败、文件格式错误

**调试文档：**

- LangGraph 断点调试：https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/breakpoints/
- LangSmith Tracing：https://docs.smith.langchain.com/

---

## 五、面试准备策略（BillMind 版）

### 5.1 面试官会关注什么

| 维度 | BillMind 可讲亮点 |
|------|-------------------|
| 理解深度 | 记账 Agent 的思考-行动循环；何时 Chain 够用、何时必须 LangGraph |
| 架构能力 | 为什么 db / rag / file 拆成独立工具；Skills 路由设计 |
| 工程实践 | MySQL 幂等、流式 SSE、HITL 大额确认、Eval 工具选择准确率 |
| 数据能力 | RAG vs Fine-tuning 在消费分类上的取舍 |

### 5.2 README 必须体现的亮点

```markdown
## 技术架构
- 架构图：前端 → FastAPI → LangGraph Agent → Tools(MySQL/RAG/File/Embedding)
- 为什么用 LangGraph 处理月报多步流程
- LlamaIndex 索引策略 vs 交易 Embedding 索引的区别

## 核心挑战
- Agent 循环终止条件（max_iterations + 无 tool_calls）
- 多工具协作：记一笔时如何避免 RAG 误触发
- 流式输出 + HITL 中断恢复方案
- CSV 批量导入的幂等与错误行处理

## 评估结果
- 工具选择准确率：XX%
- 消费分类：Prompt vs Fine-tuning 对比
- P95 响应延迟及优化（缓存汇总、并行 Send）
```

### 5.3 面试常见问题

**「Agent 和传统链式调用有什么区别？」**

→ BillMind 记一笔用 Chain 即可；月报生成（拉数据→汇总→对比预算→生成报告）必须用 LangGraph 状态图。

**「如何处理 Agent 幻觉？」**

→ 金额/笔数强制走 MySQL 工具返回；规则类问题走 RAG 并引用来源；结构化输出 + 校验失败重试。

**「RAG 和 Fine-tuning 怎么选？」**

→ 记账规则会变 → RAG；商户→分类映射稳定且数据量大 → 考虑 Fine-tuning；BillMind 里两者都做了对比实验。

**「LangGraph 状态管理怎么做？」**

→ `MessagesState` + MySQL checkpoint 存 thread；HITL 中断时状态冻结，用户确认后 `Command(resume=...)` 继续。

---

## 六、学习资源优先级

| 顺序 | 资源 | 时间 | 对应里程碑 |
|------|------|------|------------|
| 1 | https://python.langchain.com/docs/introduction/ | 30 分钟 | M0 全局认知 |
| 2 | https://python.langchain.com/docs/tutorials/ | 2 天 | M0-M2 Chain + Tool |
| 3 | https://langchain-ai.github.io/langgraph/tutorials/introduction/ | 2 天 | M4 Agent 图 |
| 4 | https://docs.llamaindex.ai/en/stable/getting_started/starter_tutorial/ | 1 天 | M6 RAG |
| 5 | https://python.langchain.com/docs/concepts/embedding_models/ | 0.5 天 | M7 Embeddings |
| 6 | https://langchain-ai.github.io/langgraph/concepts/persistence/ | 0.5 天 | M9 Memory |
| 7 | https://docs.smith.langchain.com/ | 0.5 天 | M10 Eval |
| 8 | 项目实战 | 持续 | M1-M13 增量交付 |

---

## 七、进度追踪

复制到你的笔记或 GitHub Project，每完成一项打勾：

```
第 1 周
- [ ] M0  LangChain 解析记账意图
- [ ] M1  FastAPI + MySQL CRUD
- [ ] M2  Function Calling 工具
- [ ] M3  前端聊天页（流式）
- [ ] M4  LangGraph 记账 Agent

第 2 周
- [ ] M5  CSV / 文件导入
- [ ] M6  LlamaIndex RAG 知识库
- [ ] M7  Embeddings 语义搜账单
- [ ] M8  月度报告工作流

第 3 周
- [ ] M9  Memory + HITL 大额确认
- [ ] M10 Eval + LangSmith
- [ ] M11 Agent Skills 模块化
- [ ] M12 Fine-tuning 实验（可选）
- [ ] M13 前端仪表盘
```

---

## 结语

BillMind 把 LangChain、LangGraph、LlamaIndex、Function Calling、RAG、Embeddings、Fine-tuning、Skills 串成一条真实的增量开发线——每学一个概念，项目就多一个能演示的功能。你的后端经验（API、DB、状态机）会直接迁移；需要额外适应的是 **LLM 不确定性** 带来的工具校验、Eval 和 HITL 设计。三周后你交付的不只是「会用框架」，而是一个能讲清架构权衡的全栈 Agent 项目。
