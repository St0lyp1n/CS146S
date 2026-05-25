# 待办事项提取器（Week 2）

一个基于 **FastAPI + SQLite** 的轻量 Web 应用，可将自由格式的会议笔记转换为可执行的待办列表。应用支持两种提取方式：快速的**启发式**解析器，以及基于 [Ollama](https://ollama.com/) 结构化输出的 **LLM** 提取器。

内置 HTML 前端支持粘贴笔记、提取待办、标记完成、浏览已保存笔记，无需单独的前端构建步骤。

## 功能特性

- 从 bullet 列表、复选框、关键词前缀行（`todo:`、`action:`、`next:`）中提取待办事项
- 通过 Ollama 进行可选的 LLM 提取（默认 `llama3.2:3b`），输出受 JSON Schema 约束
- 将笔记与提取出的待办事项持久化到 SQLite
- 基于 Pydantic 的 REST API 请求/响应契约
- 浏览器访问 `http://127.0.0.1:8000/` 即可使用

## 项目结构

```
week2/
├── app/
│   ├── main.py              # FastAPI 应用、生命周期、异常处理
│   ├── config.py            # 配置（路径、环境变量覆盖）
│   ├── database/            # SQLite 连接与仓储层
│   ├── routers/             # HTTP 路由处理
│   ├── schemas/             # Pydantic API 契约
│   └── services/extract.py  # 启发式 + LLM 提取逻辑
├── frontend/index.html      # 静态前端页面
├── data/app.db              # SQLite 数据库（运行时自动创建）
└── tests/                   # Pytest 测试套件
```

## 建立与运行

### 前置要求

- Python 3.10+
- [Poetry](https://python-poetry.org/)（依赖管理）
- [Ollama](https://ollama.com/download)（仅 LLM 提取时需要）

### 1. 安装依赖

在**仓库根目录**（`CS146S/`）下执行：

```bash
poetry install
```

若使用课程 conda 环境：

```bash
conda activate cs146s
poetry install
```

### 2. 拉取 Ollama 模型（用于 LLM 提取）

建议使用较小模型以降低资源占用：

```bash
ollama pull llama3.2:3b
```

使用页面上的 **Extract LLM** 按钮或调用 `/action-items/extract-llm` 接口前，请确保 Ollama 服务已启动。

### 3. 启动服务

在仓库根目录执行：

```bash
poetry run uvicorn week2.app.main:app --reload
```

在浏览器中打开 [http://127.0.0.1:8000/](http://127.0.0.1:8000/)。

### 可选环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OLLAMA_MODEL` | `llama3.2:3b` | LLM 提取使用的 Ollama 模型 |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API 地址 |
| `WEEK2_DATA_DIR` | `week2/data` | SQLite 数据目录 |
| `WEEK2_DB_PATH` | `week2/data/app.db` | SQLite 数据库文件路径 |
| `WEEK2_FRONTEND_DIR` | `week2/frontend` | 静态前端目录 |

交互式 API 文档：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)。

## API 端点及作用

### 界面

| 方法 | 路径 | 作用 |
|------|------|------|
| `GET` | `/` | 返回待办提取器 Web 页面 |
| `GET` | `/static/*` | 静态前端资源 |

### 笔记（Notes）

| 方法 | 路径 | 作用 |
|------|------|------|
| `GET` | `/notes` | 列出所有已保存笔记（按 id 降序） |
| `POST` | `/notes` | 创建笔记。请求体：`{"content": "..."}` |
| `GET` | `/notes/{note_id}` | 按 ID 获取单条笔记 |

### 待办事项（Action Items）

| 方法 | 路径 | 作用 |
|------|------|------|
| `POST` | `/action-items/extract` | 使用启发式规则提取。请求体：`{"text": "...", "save_note": false}` |
| `POST` | `/action-items/extract-llm` | 使用 Ollama LLM 提取（请求体与 `/extract` 相同） |
| `GET` | `/action-items` | 列出待办事项。可选查询参数：`?note_id=1` |
| `POST` | `/action-items/{id}/done` | 标记完成/未完成。请求体：`{"done": true}` |

#### 提取接口请求 / 响应示例

**请求**

```json
{
  "text": "- [ ] Set up database\n- Write tests",
  "save_note": true
}
```

**响应**

```json
{
  "note_id": 1,
  "items": [
    { "id": 10, "text": "Set up database" },
    { "id": 11, "text": "Write tests" }
  ]
}
```

当 `save_note` 为 `true` 时，输入文本会保存为笔记，并与创建的待办事项关联。

错误响应为 JSON 格式 `{"detail": "..."}`，常见状态码：`404`、`422`；LLM 提取在 Ollama 不可用时返回 `503`。

## 运行测试

在仓库根目录执行：

```bash
poetry run pytest week2/tests/ -v
```

仅运行提取逻辑测试：

```bash
poetry run pytest week2/tests/test_extract.py -v
```

仅运行 API 冒烟测试：

```bash
poetry run pytest week2/tests/test_api_smoke.py -v
```

当 Ollama 不可达时，与 LLM 相关的测试会自动跳过。运行这些测试前请先启动 Ollama 并拉取模型。

## 前端使用说明

1. 在文本框中粘贴笔记。
2. **Extract** — 启发式提取（`/action-items/extract`）。
3. **Extract LLM** — Ollama LLM 提取（`/action-items/extract-llm`）。
4. **List Notes** — 加载并展示所有已保存笔记（`GET /notes`）。
5. 勾选待办旁的复选框以标记完成（调用 `/action-items/{id}/done`）。

## 相关文档

- 课程作业说明：[assignment.md](./assignment.md)
- Ollama 结构化输出：https://ollama.com/blog/structured-outputs
- Ollama 模型库：https://ollama.com/library
