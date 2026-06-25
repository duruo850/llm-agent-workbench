# Examples 示例索引

本目录包含 BillMind 各阶段独立 demo，可单独运行验证。

## 示例列表

| 文件 | 说明 | LLM |
|------|------|-----|
| `00_hello_chain.py` | 自然语言入账（M0） | DeepSeek `deepseek-chat` |
| `01_image_ollama_chain.py` | 截图入账 | Ollama `qwen2.5vl:7b` |

## Ollama 平台简介

**Ollama** 是本地 LLM 运行时，类似「本机版的 OpenAI API」：

- 通过 Docker / 原生 App 在本地启动推理服务（默认 `http://localhost:11434`）
- 提供 **OpenAI 兼容 REST API**（`/v1/chat/completions`），LangChain `ChatOpenAI` 可直接对接
- **完全免费、离线可用**，数据不出本机
- 模型以 GGUF 量化格式存储，首次 `pull` 后持久化在 Docker volume

## 模型说明：`qwen2.5vl:7b`

| 属性 | 说明 |
|------|------|
| 全名 | Qwen2.5-VL 7B（阿里通义千问视觉语言模型） |
| 大小 | 约 6 GB（Q4 量化） |
| 模态 | 文本 + 图片（Vision-Language Model） |
| 上下文 | 125K tokens |
| Ollama 标签 | `qwen2.5vl:7b` |

**与本项目相关的能力：**

| 能力 | BillMind 用途 |
|------|---------------|
| 图片理解 / OCR | 读微信/支付宝账单页 |
| 结构化提取 | 提取金额、商户、说明 |
| 视觉问答 | 「从这张截图提取记账 JSON」 |
| 中文表现 | 微信截图中文界面 |
| JSON 输出 | 配合 Prompt 对接 `ParsedTransaction` |

**局限：**

- 无 Function Calling（M2 仍用 DeepSeek）
- Intel Mac CPU 推理较慢（30s+/张）
- Docker on Mac 无法使用 GPU 加速

**可选替代模型**（在 `.env` 中改 `OLLAMA_VISION_MODEL`）：

| 模型 | 大小 | 特点 |
|------|------|------|
| `qwen2.5vl:3b` | ~3 GB | 更轻，精度略低 |
| `llava:7b` | ~5 GB | 英文为主，中文弱 |
| `minicpm-v` | ~5 GB | 移动端优化，中文可用 |

## 一键安装

```bash
./examples/setup-ollama.sh          # Docker 启动 + pull 模型
docker compose -f examples/docker-compose.yml ps   # 查看状态
docker compose -f examples/docker-compose.yml logs # 查看日志
```

## 运行示例

```bash
.venv/bin/python examples/01_image_ollama_chain.py
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | OpenAI 兼容 API 地址 |
| `OLLAMA_VISION_MODEL` | `qwen2.5vl:7b` | 视觉模型标签 |

无需 API Key。

## LLM 平台抽象（`src/common/llm/`）

项目通过统一工厂将不同平台接入 LangChain：

```
examples/00_hello_chain.py  ──► get_langchain_chat_llm()           ──► LLMProvider.DEEPSEEK + TEXT
examples/01_image_ollama_chain.py ──► get_langchain_chat_llm() ──► LLMProvider.OLLAMA + VISION
                                          │
                                          ▼
                              get_langchain_chat_llm(provider, capability)
                                          │
                                          ▼
                              ChatOpenAI（OpenAI 兼容接口，LangChain 统一入口）
```

- `LLMProvider`：平台（DeepSeek / Ollama）
- `LLMCapability`：能力（TEXT / VISION）
- `ProviderSpec`：运行时 model / base_url / api_key

## 故障排查

| 问题 | 处理 |
|------|------|
| Docker 未启动 | 启动 Docker Desktop |
| 11434 端口占用 | `lsof -i :11434`，停止冲突进程或改端口 |
| 模型未 pull | `docker compose -f examples/docker-compose.yml exec ollama ollama list` |
| Intel Mac 推理超时 | 正常现象，耐心等待 30s+ |
| 想更快 | `.env` 改 `OLLAMA_VISION_MODEL=qwen2.5vl:3b` |

## API 手动测试

```bash
curl http://localhost:11434/api/tags    # 已安装模型列表
```
