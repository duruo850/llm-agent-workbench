# BillMind 意图分类器（M12）

在 LangGraph ReAct **之前**，把用户消息路由到 skill **category_id**（4 类），再绑定该分类的 tool 子集；`general_chat` 直调预置回复。

```
用户消息 → intent_manager.classify() → category_id → category 子图 / reply_general_chat → ReAct
```

本目录实现三种分类方案 + 生产默认的 **Hybrid 三级漏斗**（Rule → **BERT** → Embedding）。

---

## 目录结构

| 文件 | 方案 | 生产角色 |
|------|------|----------|
| `rule.py` | 关键词 + 正则完整匹配 | Hybrid 第一级（最快） |
| `bert.py` | BERT / sklearn 序列分类 | Hybrid **第二级** |
| `embedding.py` | Ollama 向量余弦相似度 | Hybrid 第三级 |
| `hybrid.py` | 串联上述三者 | **默认**（`intent_classifier: hybrid`） |

统一入口：`agent/intent/manager.py` → `intent_manager.classify(text)`。

---

## 方案 1：RuleClassifier（`rule.py`）

### 原理

1. 启动时 `refresh()`：从 `registry` 读取每个场景的 `keywords`、`patterns`（场景级 `register_intent_scene` + `@tool_policy` 触发语合并）。
2. 按 `CLASSIFIABLE_SCENE_IDS` **固定顺序**遍历 7 个场景。
3. 子串命中 `keywords`，或正则命中 `patterns` → 返回 `confidence=1.0, method="rule"`。
4. 全未命中 → 返回 `None`，交给下一级。

### 使用方式

```python
from agent.intent.classifiers import RuleClassifier

clf = RuleClassifier()
clf.refresh()  # 须在 init_skills() 之后
result = clf.classify("刚才咖啡花了 28 元")
# IntentResult(scene='accounting_write', confidence=1.0, method='rule')
```

```bash
# 仅 Rule
curl -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8000/intent/classify?q=本月餐饮花了多少&method=rule"

# 配置
# config.yaml: intent_classifier: rule
```

调参：改各 skill 的 `register_intent_scene(keywords=..., patterns=...)` 或 `@tool_policy(user_triggers=...)`；冲突时调整 `CLASSIFIABLE_SCENE_IDS` 顺序（`agent/agent/promt/intent_scene.py`）。

### 优缺点

| 优点 | 缺点 |
|------|------|
| 延迟 < 1ms，无外部依赖 | 泛化差，新表述需手工加规则 |
| 可解释（命中哪条 keyword/pattern） | 多场景关键词重叠时需仔细排优先级 |
| BillMind 域内高准确率（评测 100%） | 无法给出 0~1 之间的细粒度置信度 |

---

## 方案 2：EmbeddingClassifier（`embedding.py`）

### 原理

1. `warmup()`：用 Ollama `nomic-embed-text` 对每个场景的 `description` 做 `embed_query`，7 个向量缓存在内存。
2. `classify()`：用户句 embed 后与 7 个场景向量算 **余弦相似度**，取 Top-1。
3. 若 `score >= intent_embedding_threshold`（默认 0.75）→ 命中；否则 `None`。

不建 Milvus 集合；场景仅 ~8 个，内存预计算即可。

### 使用方式

```python
from agent.intent.classifiers import EmbeddingClassifier

clf = EmbeddingClassifier()
clf.warmup()  # 需要 Ollama 运行
result = clf.classify("帮我看看上个月花了多少钱")
```

```bash
# 依赖：docker compose 中 ollama 已启动
# config.yaml:
#   ollama_embedding_model: nomic-embed-text
#   intent_embedding_threshold: 0.75
#   intent_classifier: embedding
```

调参：改写场景 `description`（`register_intent_scene`）；阈值过高会误杀 → 下调 `intent_embedding_threshold`。

### 优缺点

| 优点 | 缺点 |
|------|------|
| 语义泛化，少写规则 | 依赖 Ollama；不可用则 Hybrid 自动跳过 |
| 与 M7/M8 共用 embedding 模型 | 延迟 ~10ms（含一次 embed RPC） |
| 场景少时无需向量库 | 场景描述写得差会拉低准确率 |
| 输出真实相似度分数 | 相近场景（记账 vs 查账）可能混淆 |

---

## 方案 3：BertClassifier（`bert.py`）

### 原理

1. 离线训练：`scripts/train_intent_classifier.py` 读取 `test/eval/intent_cases.json`，学习「用户句 → scene_id」。
2. `warmup()` 加载 `data/intent/bert-classifier/`：
   - 有 `sklearn_pipeline.joblib` → Tfidf + LogisticRegression（Python 3.14 默认）
   - 有 `config.json` + torch → `bert-base-chinese` transformers
3. `classify()`：`predict_proba` / softmax → Top-1，若 `>= intent_bert_threshold`（默认 0.6）→ 命中。

### 使用方式

```bash
# 训练（sklearn，无需 GPU）
.venv/bin/python3.14 scripts/train_intent_classifier.py --backend sklearn

# 有 torch 的环境
.venv/bin/python3.14 scripts/train_intent_classifier.py --backend transformers

# 评测
.venv/bin/python3.14 test/eval/run_intent_eval.py --method bert
```

```python
from agent.intent.classifiers import BertClassifier

clf = BertClassifier()
clf.warmup()
result = clf.classify("ambiguous user utterance")
```

```yaml
# config.yaml
intent_bert_threshold: 0.6
intent_bert_model_path: data/intent/bert-classifier
intent_classifier: bert
```

调参：扩充 `intent_cases.json` 后重训；阈值 `intent_bert_threshold` 控制保守程度。

### 优缺点

| 优点 | 缺点 |
|------|------|
| 有标注数据时泛化最好 | 需离线训练与权重文件 |
| 适合 Rule/Embedding 都未覆盖的表述 | transformers 版 CPU 推理 ~100–300ms |
| sklearn 版轻量、无 GPU | 新场景需重训 + 改 label 映射 |
| Hybrid 末级兜底，提升召回 | 标注不足时易过拟合 |

---

## Hybrid 漏斗（`hybrid.py`，生产默认）

### 原理

```
Rule.classify(text)
  ├─ 命中 → 返回
  └─ None → Bert.classify(text)
              ├─ 命中 → 返回
              └─ None → Embedding.classify(text)
                          ├─ 命中 → 返回
                          └─ None → fallback_all（全量 tools）
```

快路径优先：域内常见表述走 Rule（完整匹配）；Rule 未命中走本地 BERT（sklearn 快）；再不行走 Embedding；全失败保持 M11 全量 tool 行为。

### 使用方式

```yaml
# config.yaml（默认）
intent_classifier: hybrid
intent_bert_threshold: 0.8
intent_embedding_threshold: 0.7
```

```python
from agent.intent import intent_manager

intent_manager.prepare()  # Agent.init() 内已调用
result = intent_manager.classify("基金定投有什么好处")
graph_tools = intent_manager.resolve_tools(result.scene)
```

```bash
.venv/bin/python3.14 test/eval/run_intent_eval.py --method hybrid
.venv/bin/python3.14 examples/06_intent_demo.py
```

### 优缺点

| 优点 | 缺点 |
|------|------|
| 兼顾速度、泛化、召回 | 单路调试需显式 `method=rule/embedding/bert` |
| 某级不可用自动跳过（如 Ollama 挂） | 最坏情况延迟 = Rule+Embed+BERT 累加 |
| `fallback_all` 保证不漏意图 | 误分类时只能调参/扩规则/重训，无在线学习 |

---

## 与 Agent 的衔接

| 步骤 | 代码 |
|------|------|
| 分类 | `invoke_v2` → `intent_manager.classify(message)` |
| general_chat | 直调 `reply_general_chat`，不编译子图 |
| 选图 | `Agent._graph_for_category(intent.scene)` |
| 落库 | `agent_loop_runs.intent_scene / intent_method / intent_confidence` |
| 调试 API | `GET /intent/classify?q=...&method=hybrid` |

分类与 tool 的定义：

- 分类语义：`register_skill_category()`（各 `agent/skills/*.py`、`agent/mcp/__init__.py`）
- tool 归属：`@tool_policy(skill_category=...)`
- 运行时聚合：`agent/common/skill_registry.py`

---

## 验收命令

```bash
.venv/bin/python3.14 -m pytest agent/intent/ agent/common/ -v -m "not bert"
.venv/bin/python3.14 test/eval/run_intent_eval.py --method hybrid
```

目标（BillMind 域内）：Hybrid 准确率 ≥ 90%，P99 Rule 路径 < 100ms。
