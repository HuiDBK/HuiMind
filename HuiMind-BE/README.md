# HuiMind-BE

## 项目概述

HuiMind-BE 是 HuiMind AI 伴学平台的后端服务，基于 FastAPI 框架开发，提供完整的 AI 驱动学习助手功能。核心功能包括智能问答、练习出题、薄弱点追踪、艾宾浩斯复习调度等。

## 技术栈

- **框架**: FastAPI
- **语言**: Python 3.9+
- **数据库**: PostgreSQL
- **缓存**: Redis
- **向量库**: ChromaDB
- **任务队列**: Celery
- **AI 模型**: OpenAI API
- **认证**: JWT

## 目录结构

```
HuiMind-BE/
├── src/                     # 主源代码目录
│   ├── agents/              # AI 代理模块
│   ├── constants/           # 常量定义
│   ├── dao/                 # 数据访问对象
│   │   ├── orm/             # 数据库 ORM
│   │   └── redis/           # Redis 操作
│   ├── data_schemas/        # 数据模型
│   │   ├── api_schemas/     # API 接口模型
│   │   └── logic_schemas/   # 业务逻辑模型
│   ├── enums/               # 枚举类型
│   ├── handlers/            # 请求处理器
│   ├── middlewares/         # 中间件
│   ├── routes/              # 路由定义
│   ├── services/            # 业务逻辑服务
│   ├── settings/            # 配置管理
│   ├── tasks/               # 异步任务
│   ├── utils/               # 工具函数
│   └── server.py            # 服务器启动
├── main.py                  # 应用入口
├── requirements.txt         # 依赖管理
└── README.md                # 项目文档
```

## 快速开始

### 1. 环境准备

```bash
# 克隆仓库
git clone <repository-url>
cd HuiMind-BE

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置文件

创建 `.env` 文件，配置以下环境变量：

```env
# 数据库配置
DATABASE_URL="postgresql://username:password@localhost:5432/huimind"

# Redis配置
REDIS_URL="redis://localhost:6379/0"

# JWT配置
SECRET_KEY="your-secret-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI配置
OPENAI_API_KEY="your-openai-api-key"

# 其他配置
CELERY_BROKER_URL="redis://localhost:6379/1"
CELERY_RESULT_BACKEND="redis://localhost:6379/1"
```

### 3. 启动服务

```bash
# 启动应用
python main.py

# 启动 Celery  worker（另一个终端）
celery -A src.tasks.celery_app worker --loglevel=info
```

服务将在 `http://localhost:8000` 启动，API 文档可通过 `http://localhost:8000/docs` 访问。

## 核心功能

### 1. 用户认证
- 注册、登录、刷新令牌
- JWT 基于的身份验证
- 密码加密存储

### 2. 文档管理
- 上传学习资料（PDF、Word、Markdown等）
- 文档解析与切分
- 向量数据库存储
- 文档状态管理

### 3. 学习场景
- 通用学习场景
- 求职助手场景
- 考研备考场景
- 考公备考场景

### 4. RAG 系统
- 基于向量搜索的知识检索
- 上下文感知的问答
- 引用来源追踪

### 5. 复习系统
- 艾宾浩斯遗忘曲线算法
- 智能复习调度
- 薄弱点分析

### 6. AI 代理
- 学习助手代理
- 个性化学习建议
- 练习题目生成

## API 文档

项目使用 FastAPI 自动生成 API 文档，可通过以下方式访问：

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### 主要接口

| 模块 | 路径 | 功能 |
|------|------|------|
| 认证 | `/api/v1/auth/*` | 登录、注册、刷新令牌 |
| 文档 | `/api/v1/document/*` | 文档上传、管理、查询 |
| 场景 | `/api/v1/scene/*` | 学习场景管理 |
| RAG | `/api/v1/rag/*` | 知识问答、检索 |
| 复习 | `/api/v1/review/*` | 复习计划、进度管理 |
| 职业 | `/api/v1/career/*` | 求职助手功能 |

## 部署说明

### 生产环境部署

1. **构建 Docker 镜像**

```bash
# 构建镜像
docker build -t huimind-be .

# 运行容器
docker run -d --name huimind-be \
  -p 8000:8000 \
  --env-file .env \
  huimind-be
```

2. **使用 docker-compose**

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis
  worker:
    build: .
    command: celery -A src.tasks.celery_app worker --loglevel=info
    env_file:
      - .env
    depends_on:
      - redis
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: huimind
      POSTGRES_USER: username
      POSTGRES_PASSWORD: password
  redis:
    image: redis:7
```

### 监控与日志

- **日志**: 使用 Python 标准日志模块，配置在 `src/settings/log_setting.py`
- **监控**: 可集成 Prometheus + Grafana 进行系统监控

## 开发规范

### 代码风格

- 遵循 PEP 8 代码规范
- 使用 Black 进行代码格式化
- 使用 Ruff 进行代码检查

### 项目结构规范

- **routes 层**: 只负责路由注册，继承 `BaseAPIRouter`
- **handlers 层**: 负责参数校验、调用 service，继承 `BaseHandler`
- **service 层**: 负责具体业务逻辑，继承 `BaseService`
- **manager 层**: 负责数据库查询，继承 `BaseManager`

### 接口响应格式

统一响应格式为 `code`、`message`、`data` 三层结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "key": "value"
  }
}
```

分页响应格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 100,
    "data_list": [...] 
  }
}
```

### 注释规范

- 模块级注释：每个模块必须有模块 docstring
- 类 docstring：所有业务类、基类必须有类 docstring
- 函数/方法 docstring：所有复杂函数、对外可调用函数必须有 docstring
- 遵循 Google Python Style Guide 注释风格

## 测试

### 运行测试

```bash
# 运行单元测试
python -m pytest

# 运行特定测试文件
python -m pytest test_llm.py -v
```

### 测试覆盖

- 核心功能模块应有单元测试
- API 接口应有集成测试
- 关键业务逻辑应有边界测试

## 贡献指南

1. **Fork 仓库**
2. **创建分支** (`git checkout -b feature/your-feature`)
3. **提交更改** (`git commit -m 'Add some feature'`)
4. **推送到分支** (`git push origin feature/your-feature`)
5. **创建 Pull Request**

## 许可证

本项目采用 MIT 许可证。

## 联系方式

- 项目维护者: HuiMind Team
- 邮箱: contact@huimind.ai
- 官方网站: https://huimind.ai
