# 命名约定

## ORM 实体类

| 实体 | 类名 | 表名 |
|------|------|------|
| 分类 | `Category` | `categories` |
| 预算 | `Budget` | `budgets` |
| 交易 | `Transaction` | `transactions` |

**禁止** `CategoryTable`、`TransactionTable` 等 `*Table` 后缀。

## Request / Response

| 用途 | 命名 | 位置 |
|------|------|------|
| 创建 | `{Entity}CreateRequest` | `server/model/request/{entity}.py` |
| 更新 | `{Entity}UpdateRequest` | 同上 |
| 查询 | `{Entity}ListQueryRequest` 等 | 同上 |
| 单条 GET | `{Entity}GetResponse` | `server/model/response/{entity}.py` |
| 列表项 | `{Entity}ListResponse` | 自定义列表返回 |
| 汇总类 | `MonthlySummaryResponse` 等 | `server/model/response/summary.py` |

FastCRUD `select_schema` 使用 `{Entity}GetResponse`。

## LLM 解析

| 用途 | 命名 | 位置 |
|------|------|------|
| 解析结构 | `ParsedTransaction` | [`server/model/request/parsed.py`](../../server/model/request/parsed.py) |
| M0 示例别名 | `Transaction = ParsedTransaction` | 仅 examples 兼容，**新代码优先 ParsedTransaction** |

## FastCRUD 路由与响应

- 标准 CRUD 路径：`/categories`、`/budgets`、`/transactions/{id}` 等由 FastCRUD 生成
- 列表：`GET /categories` 返回 `{ "data": [...] }`；`total_count` 视 FastCRUD 版本可有可无
- `PATCH` 可能返回**空 body**，测试应再 `GET` 校验
- `POST` 创建返回完整 `{Entity}GetResponse` 形状（视 FastCRUD 配置）

## API 自定义路由

| 路由 | 说明 |
|------|------|
| `GET /transactions?month=` | 自定义，返回 `list[TransactionListResponse]`（非 FastCRUD 分页包装） |
| `GET /summary/monthly?month=` | 月度汇总 |

## 环境变量

见 [`.env.example`](../../.env.example)：`DATABASE_URL`、`DEEPSEEK_API_KEY`、`API_BASE_URL`（测试）、Ollama 相关。

## 日志

- 请求：logger 名 `billmind.request`（[`server/main.py`](../../server/main.py) 中间件）
- 数据库：logger 名 `billmind.db`（[`server/db/migrate.py`](../../server/db/migrate.py)）
