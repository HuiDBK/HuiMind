# HuiMind-AI 伴学平台

## 产品概述

AI 伴学平台是一款面向个人用户的 AI 驱动学习助手，核心差异化是「有记忆、会追踪、能主动推送、有趣到停不下来」。用户上传自己的学习资料，平台提供智能问答、练习出题、薄弱点追踪、艾宾浩斯复习调度，并通过飞书/QQ 机器人在碎片时间触达用户。

产品采用「统一 Agent 引擎 + 场景配置层」架构，MVP 内置三个官方场景（求职助手、考研备考、考公备考），同时提供通用学习底座和用户自建场景能力。平台收集用户行为数据，驱动官方场景持续迭代——这是产品的数据飞轮。

## 本地启动指南（前端 + 后端）

面向第一次运行项目的新同学：按本文档步骤执行，可独立完成本地环境搭建、服务启动与前后端联调。

### 目录

1. 环境要求
2. 快速开始（推荐流程）
3. 后端启动（HuiMind-BE）
4. Celery 异步任务（可选但推荐）
5. 前端启动（HuiMind-FE）
6. 前后端联调说明
7. 开发模式 vs 生产模式
8. 服务验证方法
9. 常见启动错误与解决方案
10. Docker（可选）

### 1. 环境要求

**操作系统**
- macOS / Linux / Windows（本文命令以 macOS/Linux 为例）

**前端**
- Node.js：建议 20.x LTS（最低建议 18.18+）
- 包管理器：npm（默认）或 pnpm/yarn

**后端**
- Python：建议 3.11.x（项目已在 3.11 环境下验证）
- pip：建议 23+

**依赖服务**
- Redis：建议 7.x（Celery broker/backend、会话历史；不启动也能跑通基础 API，但会影响异步解析与历史记忆）
- SQLite：无需单独安装（本项目 MVP 使用 SQLite 文件模拟数据库）

### 2. 快速开始（推荐流程）

按顺序执行：

1) 启动 Redis  
2) 启动后端（FastAPI）  
3)（可选）启动 Celery Worker（用于“上传→异步切分入库”）  
4) 启动前端（Next.js）并配置 API_BASE_URL  

### 3. 后端启动（HuiMind-BE）

#### 3.1 进入目录

```bash
cd HuiMind-BE
```

#### 3.2 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3.3 配置环境变量

后端从环境变量读取配置，核心项在 `src/settings/base_setting.py`：

- `SERVER_HOST`（默认 `127.0.0.1`）
- `SERVER_PORT`（默认 `8000`）
- `OPENAI_API_KEY`（必填：用于 Agent/Embedding）
- `OPENAI_API_BASE`（必填：OpenAI 兼容网关地址；代码会自动补 `/v1`）
- `MODEL_NAME`（默认 `gpt-5.4`）
- `EMBEDDING_MODEL_NAME`（默认 `text-embedding-3-small`）
- `CHROMA_PERSIST_DIR`（默认 `./chroma_db`）
- `FILE_STORAGE_DIR`（默认 `./uploads`）

示例（仅示意，建议写入你的 shell profile 或启动命令前 export）：

```bash
export OPENAI_API_KEY="你的key"
export OPENAI_API_BASE="https://zapi.aicc0.com/"
export MODEL_NAME="gpt-5.4"
```

#### 3.4 启动后端服务

开发模式（自动 reload）：

```bash
python main.py
```

预期输出（示例）：

```text
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

后端地址与文档：
- API Base：`http://127.0.0.1:8000/api/v1`
- OpenAPI 文档：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/api/v1/health`

#### 3.5 数据库与本地文件说明

- SQLite 文件：后端会自动创建 `task_flow.db`（默认在 `HuiMind-BE/` 目录）
- 上传文件落盘：默认在 `HuiMind-BE/uploads/`（可通过 `FILE_STORAGE_DIR` 修改）
- 向量库持久化：默认在 `HuiMind-BE/chroma_db/`（可通过 `CHROMA_PERSIST_DIR` 修改）

### 4. Celery 异步任务（可选但推荐）

用途：用于“资料上传后异步解析/切分/向量化入库”。如果不启动 Celery，接口仍可用，但新上传资料可能不会自动进入向量库。

#### 4.1 确保 Redis 已启动

默认连接：`redis://127.0.0.1:6379/0`

#### 4.2 启动 Worker

在 `HuiMind-BE` 目录下新开一个终端：

```bash
celery -A src.tasks.celery_app.celery_app worker -l info
```

预期输出（示例）：

```text
[tasks]
  . src.tasks.document.parse_document_task
```

### 5. 前端启动（HuiMind-FE）

#### 5.1 进入目录并安装依赖

```bash
cd HuiMind-FE
npm install
```

#### 5.2 配置后端 API 地址（联调必做）

前端默认读取：
- `NEXT_PUBLIC_API_BASE_URL`（默认 `http://127.0.0.1:8000/api/v1`）

建议创建 `HuiMind-FE/.env.local`：

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

#### 5.3 启动前端服务

开发模式：

```bash
npm run dev -- -p 3001
```

打开页面：
- `http://127.0.0.1:3001`

说明：后端已默认放行 `3000/3001/3002` 作为 CORS 允许来源。

### 6. 前后端联调说明

**联调关键点**
- 前端必须指向后端的 `/api/v1`：例如 `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1`
- 前端端口建议使用 `3000~3002`（后端 CORS 默认允许）

**登录与默认账号**
- 登录页：`/login`
- MVP 默认账号：`demo@huimind.ai`
- 默认密码：`123456`

### 7. 开发模式 vs 生产模式

**后端**
- 开发模式：`python main.py`（reload=True）
- 生产模式：建议使用 `uvicorn main:app --host 0.0.0.0 --port 8000`（关闭 reload，自行管理进程）

**前端**
- 开发模式：`npm run dev -- -p 3001`
- 生产模式：
  1) `npm run build`
  2) `npm run start -- -p 3001`

### 8. 服务验证方法

**后端是否成功启动**

```bash
curl -s http://127.0.0.1:8000/api/v1/health
```

预期返回（示例）：

```json
{"code":0,"message":"ok","data":{"status":"ok"}}
```

**LLM 连通性验证（推荐）**

后端目录下提供了连通性脚本：

```bash
cd HuiMind-BE
python test_llm.py
```

**问答接口验证**

```bash
curl -s http://127.0.0.1:8000/api/v1/qa/ask \
  -H 'Content-Type: application/json' \
  -d '{"scene_id":"general","session_id":1,"question":"用一句中文回答：你是谁？"}'
```

**流式接口验证（SSE）**

```bash
curl -N http://127.0.0.1:8000/api/v1/qa/ask_stream \
  -H 'Content-Type: application/json' \
  -d '{"scene_id":"general","session_id":1,"question":"请先检索知识库，回答：Redis 缓存穿透与击穿的区别？"}'
```

### 9. 常见启动错误与解决方案

#### 9.1 前端请求失败：Failed to fetch / CORS

现象：
- 浏览器控制台报 `Failed to fetch` 或 `net::ERR_FAILED`

排查：
1) 确认 `NEXT_PUBLIC_API_BASE_URL` 指向了正确地址（必须包含 `/api/v1`）
2) 确认前端端口在 `3000/3001/3002` 范围内
3) 确认后端已启动且可访问 `/api/v1/health`

#### 9.2 Redis 连接失败：Connection refused

现象：
- 问答历史/异步任务报 Redis 连接错误

解决：
- 启动 Redis（见下方 Docker 或本地安装方式）

#### 9.3 LLM 401：invalid_api_key / 无效令牌

现象：
- `/qa/ask` 报错或返回提示“请检查 OPENAI_API_KEY…”

排查：
1) 确认 `OPENAI_API_KEY` 正确可用
2) 确认 `OPENAI_API_BASE` 是 OpenAI 兼容接口地址（代码会自动补 `/v1`）
3) 确认 `MODEL_NAME` 在该网关下真实存在

#### 9.4 端口被占用：Address already in use

解决：
- 修改端口启动（前端 `-p 3001`；后端设置 `SERVER_PORT`）
- 或关闭占用端口的进程

#### 9.5 SSE 流式请求被中断（curl: (28)/(18)）

说明：
- SSE 会持续输出 token 与 tool step；如果你用了 `--max-time` 或 `| head`，可能会提前断开，属于正常现象。

建议：
- 不要对 SSE 使用 `| head` 截断；或提高 `--max-time`。

### 10. Docker（可选）

当前仓库未提供完整的 Dockerfile / docker-compose（如需可后续补齐）。你可以先用 Docker 启动 Redis：

```bash
docker run --name huimind-redis -d -p 6379:6379 redis:7-alpine
```

停止与清理：

```bash
docker stop huimind-redis && docker rm huimind-redis
```
