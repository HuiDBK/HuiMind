# HuiMind MVP 技术设计文档（通用学习平台 + AI 学习搭子 / MySQL）

## 1. 文档目标

本文档用于定义 HuiMind 首版 MVP 的工程实现方案，确保协作者可以直接按文档开展开发。本文档统一采用以下前提：

- 首版交付形态为 `Web-only`
- 首版官方场景包含 `general` 与 `career`
- 通用学习平台能力先于垂直场景能力
- AI 学习搭子属于首版核心功能
- 关系数据库统一使用 `MySQL`
- `Redis` 与 `Celery` 属于首版必备基础设施

## 2. 架构概览

### 2.1 技术栈

| 层级 | 方案 | 说明 |
| --- | --- | --- |
| 前端 | Next.js | Web 界面、页面路由、表单与状态展示 |
| 后端 | FastAPI | API、业务编排、鉴权、模型调用 |
| 关系库 | MySQL | 用户、场景、文档元数据、问答记录、搭子配置、诊断和复习任务 |
| 向量库 | Chroma | 文档切块向量存储与检索 |
| 缓存与会话 | Redis | 用户会话上下文、热点缓存、Celery Broker/结果存储 |
| 异步任务 | Celery | 文档解析、切块向量化、重任务模型调用 |
| 定时调度 | Celery Beat | 到期复习任务扫描、搭子提醒生成 |
| LLM | OpenAI 兼容模型接口 | 问答、搭子对话、诊断、面试出题、评分、薄弱点抽取 |

### 2.2 首版核心技术取舍

- 首版必须落地 Redis，用于短期会话、缓存和任务系统依赖。
- 首版必须落地 Celery，用于文档解析和复习调度。
- 首版采用 `general` 作为通用学习默认场景，`career` 作为首个官方垂直场景。
- 场景能力共享同一套知识库、问答、记忆、复习和搭子底座。
- Web 是唯一交互入口，不引入飞书和 QQ 渠道。

## 3. 系统边界

### 3.1 入口边界

- Web 是唯一入口。
- 不接入飞书、QQ、短信、邮件回调。

### 3.2 场景边界

- 首版官方场景包含：
  - `general`：通用学习场景
  - `career`：求职场景
- 不支持用户自建场景。
- 不支持场景广场和场景 Fork。

### 3.3 数据边界

- 每个用户拥有独立私有资料空间。
- 文档、问答、薄弱点、搭子记忆、复习任务均按 `user_id + scene_id` 做隔离。
- 不允许跨用户检索、跨用户读取搭子上下文、跨用户访问面试与诊断结果。

## 4. 后端模块设计

### 4.1 模块划分

| 模块 | 职责 |
| --- | --- |
| `common` | 配置、日志、错误码、统一响应、基础工具 |
| `auth` | 登录、用户信息、开发期身份注入 |
| `scenes` | 场景列表、场景元信息、默认场景管理 |
| `documents` | 文件上传、JD 录入、文档状态、解析与向量入库 |
| `rag` | 检索、引用组织、拒答策略、问答记录 |
| `memory_review` | 薄弱点、复习任务、复习状态更新 |
| `buddy` | AI 学习搭子配置、对话、长期偏好与提醒文案 |
| `career` | 简历诊断、模拟面试、结构化反馈 |
| `tasks` | Celery 任务定义、Celery Beat 调度任务 |

### 4.2 分层建议

- `routes`：HTTP 接口层
- `handlers`：参数协调与接口编排
- `services`：核心业务逻辑
- `dao`：MySQL、Redis、Chroma 访问
- `tasks`：Celery 任务
- `data_schemas/api_schemas`：请求与响应 schema
- `data_schemas/logic_schemas`：内部结构化对象

## 5. 核心流程时序

### 5.1 文档上传流

1. 前端调用 `POST /documents/upload` 上传 PDF、TXT 或 Markdown。
2. 后端写入 `documents` 表，状态为 `uploaded`。
3. 后端投递 Celery 任务，状态更新为 `parsing`。
4. Celery Worker 执行文本提取、切块、Embedding、Chroma 写入。
5. 写入 `document_chunks_meta`，并更新 `documents.status=ready`。
6. 失败时更新 `documents.status=failed` 并记录 `error_message`。

### 5.2 问答流

1. 前端调用 `POST /qa/ask` 提交问题和 `scene_id`。
2. 后端从 Redis 读取当前用户短期会话上下文。
3. 检索层按 `user_id + scene_id` 检索 Chroma。
4. 组装引用与上下文后调用 LLM。
5. 若召回不足或证据不充分，返回拒答结果。
6. 问答结果写入 `qa_sessions` 与 `qa_messages`。
7. 同步更新 Redis 会话缓存。
8. 异步触发薄弱点分析任务，更新 `weak_points` 与 `review_tasks`。

### 5.3 AI 学习搭子流

1. 前端调用 `POST /buddy/chat` 发送消息。
2. 后端读取 `study_buddies` 配置、最近问答、薄弱点、复习任务和 Redis 会话上下文。
3. 组装搭子人格提示词并调用 LLM。
4. 返回搭子回复，同时写入 `buddy_messages`。
5. 将本轮会话摘要写入 Redis，长期偏好写入 MySQL。

### 5.4 简历诊断流

1. 前端调用 `POST /career/resume-diagnosis`，传入简历文档与 JD 文档。
2. 后端校验两份文档均处于 `scene_id=career` 且状态为 `ready`。
3. 规则层先做关键词匹配和缺失项分析。
4. 调用 LLM 生成结构化诊断结果。
5. 结果写入 `resume_diagnoses`。
6. 异步抽取薄弱点并生成复习任务。

### 5.5 模拟面试流

1. 前端调用 `POST /career/interview/sessions` 创建面试 Session。
2. 后端基于 JD 内容生成首批问题并写入 `interview_sessions`、`interview_turns`。
3. 前端调用 `POST /career/interview/sessions/{id}/answer` 逐题提交答案。
4. 后端调用 LLM 按 rubric 评分并返回反馈。
5. 评分结果写入 `interview_turns`。
6. 异步抽取薄弱点并更新 `review_tasks`。

### 5.6 薄弱点更新流

1. 问答、搭子总结、简历诊断、面试评分任一流程触发薄弱点分析。
2. 后端按 `user_id + scene_id + concept` 查找已有记录。
3. 已存在则更新错误次数、正确率、最近出现时间和复习时间。
4. 不存在则新增 `weak_points`。

### 5.7 复习任务调度流

1. Celery Beat 周期性扫描 `weak_points.next_review_at <= now()` 的记录。
2. 若不存在待处理任务，则创建 `review_tasks`。
3. 前端在复习页展示任务。
4. 用户完成任务后调用完成接口。
5. 后端根据 `mastered` 或 `review_again` 重算下一次复习时间。

### 5.8 搭子提醒生成流

1. Celery Beat 每日扫描未完成复习任务和最近活跃情况。
2. 若用户超过阈值未复习或未互动，则触发搭子提醒生成任务。
3. 提醒文案写入 `buddy_reminders`，供 Dashboard 和搭子页展示。

## 6. 数据库设计（MySQL）

### 6.1 主键策略

- 所有业务表统一使用 `BIGINT UNSIGNED AUTO_INCREMENT` 作为主键。
- 时间字段统一使用 `DATETIME`。
- 结构化结果优先使用 `JSON` 字段。

### 6.2 核心表清单

| 表名 | 说明 |
| --- | --- |
| `users` | 用户基础信息 |
| `scenes` | 官方场景定义，首版包含 `general` 和 `career` |
| `documents` | 文档元数据与处理状态 |
| `document_chunks_meta` | 文档切块来源信息 |
| `qa_sessions` | 问答会话 |
| `qa_messages` | 问答消息 |
| `study_buddies` | AI 学习搭子配置与长期状态 |
| `buddy_messages` | 搭子对话记录 |
| `buddy_reminders` | 搭子提醒记录 |
| `resume_diagnoses` | 简历诊断记录 |
| `interview_sessions` | 模拟面试会话 |
| `interview_turns` | 面试逐题记录 |
| `weak_points` | 薄弱点记录 |
| `review_tasks` | 复习任务 |

### 6.3 表结构定义

#### `users`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 用户 ID |
| `email` | VARCHAR(128) | NOT NULL, UNIQUE | 登录邮箱 |
| `nickname` | VARCHAR(64) | NOT NULL | 昵称 |
| `password_hash` | VARCHAR(255) | NULL | 开发期可为空 |
| `status` | VARCHAR(32) | NOT NULL DEFAULT 'active' | 用户状态 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

#### `scenes`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 主键 |
| `scene_id` | VARCHAR(64) | NOT NULL, UNIQUE | `general` 或 `career` |
| `name` | VARCHAR(64) | NOT NULL | 场景名称 |
| `description` | VARCHAR(255) | NOT NULL | 场景描述 |
| `system_prompt` | TEXT | NOT NULL | 场景系统提示词 |
| `enabled_tools` | JSON | NOT NULL | 允许使用的工具列表 |
| `status` | VARCHAR(32) | NOT NULL DEFAULT 'active' | 场景状态 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

#### `documents`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 文档 ID |
| `user_id` | BIGINT UNSIGNED | NOT NULL | 所属用户 |
| `scene_id` | VARCHAR(64) | NOT NULL | 所属场景 |
| `doc_type` | VARCHAR(32) | NOT NULL | `resume` / `jd` / `material` / `note` |
| `filename` | VARCHAR(255) | NULL | 原始文件名 |
| `source_url` | VARCHAR(1024) | NULL | 外部来源 |
| `storage_path` | VARCHAR(1024) | NULL | 文件存储路径 |
| `content_text` | LONGTEXT | NULL | 解析文本 |
| `status` | VARCHAR(32) | NOT NULL | `uploaded` / `parsing` / `ready` / `failed` |
| `summary` | TEXT | NULL | 文档摘要 |
| `error_message` | TEXT | NULL | 解析失败信息 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

索引：

- `idx_documents_user_scene_status (user_id, scene_id, status)`

#### `document_chunks_meta`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 主键 |
| `document_id` | BIGINT UNSIGNED | NOT NULL | 关联文档 |
| `chunk_index` | INT UNSIGNED | NOT NULL | 块序号 |
| `chroma_document_id` | VARCHAR(128) | NOT NULL, UNIQUE | Chroma 文档标识 |
| `source_label` | VARCHAR(255) | NOT NULL | 例如文件名 |
| `source_locator` | VARCHAR(255) | NULL | 页码、段落或块位置 |
| `token_count` | INT UNSIGNED | NULL | 块长度估计 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |

#### `qa_sessions`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 会话 ID |
| `user_id` | BIGINT UNSIGNED | NOT NULL | 所属用户 |
| `scene_id` | VARCHAR(64) | NOT NULL | 所属场景 |
| `title` | VARCHAR(255) | NULL | 会话标题 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

#### `qa_messages`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 消息 ID |
| `session_id` | BIGINT UNSIGNED | NOT NULL | 所属会话 |
| `role` | VARCHAR(32) | NOT NULL | `user` / `assistant` |
| `content` | LONGTEXT | NOT NULL | 消息内容 |
| `citations_json` | JSON | NULL | 引用列表 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |

#### `study_buddies`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 主键 |
| `user_id` | BIGINT UNSIGNED | NOT NULL, UNIQUE | 所属用户 |
| `name` | VARCHAR(64) | NOT NULL | 搭子名称 |
| `persona` | VARCHAR(32) | NOT NULL | `gentle` / `strict` / `energetic` / `calm` |
| `tone_prompt` | TEXT | NOT NULL | 人设提示词 |
| `memory_summary` | TEXT | NULL | 长期记忆摘要 |
| `last_interaction_at` | DATETIME | NULL | 最近互动时间 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

#### `buddy_messages`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 主键 |
| `buddy_id` | BIGINT UNSIGNED | NOT NULL | 所属搭子 |
| `scene_id` | VARCHAR(64) | NOT NULL | 对话场景 |
| `role` | VARCHAR(32) | NOT NULL | `user` / `assistant` |
| `content` | LONGTEXT | NOT NULL | 消息内容 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |

#### `buddy_reminders`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 主键 |
| `user_id` | BIGINT UNSIGNED | NOT NULL | 所属用户 |
| `scene_id` | VARCHAR(64) | NOT NULL | 提醒场景 |
| `content` | TEXT | NOT NULL | 提醒文案 |
| `status` | VARCHAR(32) | NOT NULL DEFAULT 'pending' | `pending` / `shown` / `archived` |
| `trigger_type` | VARCHAR(32) | NOT NULL | `inactive` / `review_due` / `encourage` |
| `created_at` | DATETIME | NOT NULL | 创建时间 |

#### `resume_diagnoses`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 诊断记录 ID |
| `user_id` | BIGINT UNSIGNED | NOT NULL | 所属用户 |
| `scene_id` | VARCHAR(64) | NOT NULL DEFAULT 'career' | 固定为 `career` |
| `resume_doc_id` | BIGINT UNSIGNED | NOT NULL | 简历文档 |
| `jd_doc_id` | BIGINT UNSIGNED | NOT NULL | JD 文档 |
| `match_score` | DECIMAL(5,2) | NOT NULL | 匹配度 |
| `matched_keywords_json` | JSON | NOT NULL | 命中关键词 |
| `missing_keywords_json` | JSON | NOT NULL | 缺失关键词 |
| `risky_phrases_json` | JSON | NOT NULL | 风险表达 |
| `rewrite_suggestions_json` | JSON | NOT NULL | 改写建议 |
| `summary` | TEXT | NULL | 总结 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |

#### `interview_sessions`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 面试 Session ID |
| `user_id` | BIGINT UNSIGNED | NOT NULL | 所属用户 |
| `scene_id` | VARCHAR(64) | NOT NULL DEFAULT 'career' | 固定为 `career` |
| `jd_doc_id` | BIGINT UNSIGNED | NOT NULL | 关联 JD |
| `mode` | VARCHAR(32) | NOT NULL DEFAULT 'standard' | 面试模式 |
| `status` | VARCHAR(32) | NOT NULL DEFAULT 'in_progress' | `in_progress` / `completed` |
| `overall_score` | DECIMAL(5,2) | NULL | 总评分 |
| `summary` | TEXT | NULL | 整体评语 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

#### `interview_turns`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 主键 |
| `session_id` | BIGINT UNSIGNED | NOT NULL | 面试会话 |
| `question_order` | INT UNSIGNED | NOT NULL | 题目顺序 |
| `question` | TEXT | NOT NULL | 面试题目 |
| `answer` | LONGTEXT | NULL | 用户回答 |
| `score` | DECIMAL(5,2) | NULL | 当前题得分 |
| `feedback_json` | JSON | NULL | 维度评分与建议 |
| `weak_points_json` | JSON | NULL | 识别出的薄弱点 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

索引：

- `idx_interview_turns_session_id (session_id)`

#### `weak_points`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 主键 |
| `user_id` | BIGINT UNSIGNED | NOT NULL | 所属用户 |
| `scene_id` | VARCHAR(64) | NOT NULL | 所属场景 |
| `concept` | VARCHAR(255) | NOT NULL | 薄弱点名称 |
| `source_type` | VARCHAR(32) | NOT NULL | `qa` / `buddy` / `diagnosis` / `interview` |
| `wrong_count` | INT UNSIGNED | NOT NULL DEFAULT 0 | 触发次数 |
| `correct_rate` | DECIMAL(5,2) | NOT NULL DEFAULT 0 | 正确率 |
| `mastery_level` | VARCHAR(32) | NOT NULL DEFAULT 'weak' | `weak` / `reviewing` / `stable` |
| `last_seen_at` | DATETIME | NOT NULL | 最近出现时间 |
| `next_review_at` | DATETIME | NOT NULL | 下次复习时间 |
| `metadata_json` | JSON | NULL | 来源补充信息 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

索引：

- `idx_weak_points_user_scene_next_review (user_id, scene_id, next_review_at)`
- 唯一约束建议：`uniq_weak_points_user_scene_concept (user_id, scene_id, concept)`

#### `review_tasks`

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `id` | BIGINT UNSIGNED | PK | 主键 |
| `user_id` | BIGINT UNSIGNED | NOT NULL | 所属用户 |
| `scene_id` | VARCHAR(64) | NOT NULL | 所属场景 |
| `weak_point_id` | BIGINT UNSIGNED | NOT NULL | 关联薄弱点 |
| `due_at` | DATETIME | NOT NULL | 到期时间 |
| `status` | VARCHAR(32) | NOT NULL DEFAULT 'pending' | `pending` / `completed` / `skipped` |
| `result` | VARCHAR(32) | NULL | `mastered` / `review_again` |
| `completed_at` | DATETIME | NULL | 完成时间 |
| `created_at` | DATETIME | NOT NULL | 创建时间 |
| `updated_at` | DATETIME | NOT NULL | 更新时间 |

索引：

- `idx_review_tasks_user_status_due_at (user_id, status, due_at)`

## 7. Redis 与 Celery 设计

### 7.1 Redis Key 设计

| Key 模式 | 说明 |
| --- | --- |
| `session:qa:{user_id}:{scene_id}` | 问答短期上下文 |
| `session:buddy:{user_id}:{scene_id}` | 搭子对话短期上下文 |
| `cache:documents:{user_id}:{scene_id}` | 文档列表缓存 |
| `task:status:{task_id}` | 异步任务状态 |

### 7.2 Celery 任务清单

| 任务名 | 用途 |
| --- | --- |
| `parse_document_task` | 解析文档、切块、Embedding、写入 Chroma |
| `extract_weak_points_task` | 从问答、诊断、面试结果中抽取薄弱点 |
| `generate_review_tasks_task` | 根据薄弱点生成复习任务 |
| `generate_buddy_reminders_task` | 生成搭子提醒文案 |
| `run_resume_diagnosis_task` | 重型诊断任务异步执行时使用 |

### 7.3 Celery Beat 调度

| 调度任务 | 周期 | 用途 |
| --- | --- | --- |
| `scan_due_reviews` | 每 10 分钟 | 扫描到期薄弱点并创建复习任务 |
| `scan_inactive_users` | 每天 09:00 | 为低活跃用户生成搭子提醒 |
| `cleanup_expired_sessions` | 每天 03:00 | 清理 Redis 过期上下文 |

## 8. API 设计

### 8.1 统一响应结构

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

### 8.2 错误码建议

| 错误码 | 含义 |
| --- | --- |
| `0` | 成功 |
| `40001` | 参数错误 |
| `40004` | 资源不存在 |
| `40009` | 文档状态不允许当前操作 |
| `40022` | 文件类型不支持 |
| `40023` | 文件大小超限 |
| `40040` | 资料不足，无法回答 |
| `40041` | 场景不匹配 |
| `50000` | 系统内部错误 |
| `50010` | 模型调用失败 |
| `50020` | 向量检索失败 |
| `50030` | 异步任务执行失败 |

### 8.3 接口清单

#### `POST /auth/login`

用途：用户登录。

#### `GET /me`

用途：获取当前登录用户信息。

#### `GET /scenes`

用途：获取首版可用官方场景列表。

响应体字段：

- `scene_id`
- `name`
- `description`

#### `POST /documents/upload`

用途：上传学习资料。

请求：

- `multipart/form-data`
- 字段：
  - `file`
  - `scene_id`
  - `doc_type`

#### `POST /documents/jd`

用途：在 `career` 场景录入 JD 文本或 URL。

请求体：

```json
{
  "scene_id": "career",
  "title": "后端开发工程师",
  "content": "JD 文本，可与 source_url 二选一",
  "source_url": null
}
```

#### `GET /documents`

用途：获取文档列表。

查询参数：

- `scene_id`
- `doc_type`
- `status`

#### `POST /qa/ask`

用途：在指定场景进行知识问答。

请求体：

```json
{
  "scene_id": "general",
  "session_id": 1,
  "question": "请根据我上传的资料总结这章重点"
}
```

响应体字段：

- `session_id`
- `answer`
- `citations`
- `insufficient_context`

#### `GET /buddy/profile`

用途：获取当前用户的 AI 学习搭子配置。

#### `POST /buddy/profile`

用途：创建或更新 AI 学习搭子配置。

请求体：

```json
{
  "name": "小智",
  "persona": "gentle"
}
```

#### `POST /buddy/chat`

用途：与 AI 学习搭子对话。

请求体：

```json
{
  "scene_id": "general",
  "message": "我最近总记不住这部分内容，帮我梳理一下"
}
```

响应体字段：

- `reply`
- `memory_summary`
- `suggested_actions`

#### `GET /review/tasks`

用途：获取复习任务。

查询参数：

- `scene_id`
- `status`

#### `POST /review/tasks/{id}/complete`

用途：完成复习任务。

请求体：

```json
{
  "result": "mastered"
}
```

#### `GET /memory/weak-points`

用途：获取薄弱点列表。

查询参数：

- `scene_id`

#### `POST /career/resume-diagnosis`

用途：在 `career` 场景执行简历诊断。

请求体：

```json
{
  "scene_id": "career",
  "resume_doc_id": 10,
  "jd_doc_id": 20
}
```

#### `POST /career/interview/sessions`

用途：创建模拟面试 Session。

请求体：

```json
{
  "scene_id": "career",
  "jd_doc_id": 20,
  "mode": "standard"
}
```

#### `GET /career/interview/sessions/{id}`

用途：获取面试 Session 详情。

#### `POST /career/interview/sessions/{id}/answer`

用途：提交一道面试题答案并获取反馈。

## 9. AI / LLM 设计

### 9.1 通用 RAG 检索流程

1. 对用户问题进行标准化。
2. 从 MySQL 读取当前用户、当前场景下的可用文档。
3. 以 `user_id + scene_id` 过滤 Chroma 检索范围。
4. 召回 TopK 文档块。
5. 将引用块映射回 `document_chunks_meta`。
6. 组装提示词并调用模型。
7. 输出答案及引用。

### 9.2 引用返回格式

```json
[
  {
    "document_id": 10,
    "source_label": "notes.pdf",
    "source_locator": "chunk-3",
    "quote": "支持异步任务队列进行文档处理"
  }
]
```

### 9.3 拒答策略

满足以下任一条件时返回拒答：

- 当前场景没有可用资料
- 检索结果为空
- 证据不足以支撑可靠回答
- 用户问题超出当前资料边界

### 9.4 AI 学习搭子设计

搭子最小能力：

- 拥有固定名字和人设
- 能记住用户近期学习主题和常见问题
- 能结合薄弱点和复习任务生成反馈
- 能输出鼓励、提醒和复盘文案

搭子提示词输入来源：

- `study_buddies.memory_summary`
- 最近问答记录
- 最近薄弱点
- 最近复习任务
- 当前场景信息

### 9.5 简历诊断结构化输出 Schema

```json
{
  "match_score": 78.5,
  "matched_keywords": ["Python", "FastAPI", "MySQL"],
  "missing_keywords": ["微服务", "高并发"],
  "risky_phrases": [
    {
      "original": "负责一些后端开发工作",
      "reason": "表述泛化，缺少动作和结果"
    }
  ],
  "rewrite_suggestions": [
    {
      "original": "负责一些后端开发工作",
      "rewritten": "负责 FastAPI 后端接口开发与 MySQL 数据建模，支持核心业务模块上线"
    }
  ],
  "summary": "你的经历与目标岗位基础匹配较高，但需要补足项目结果表达。"
}
```

### 9.6 模拟面试评分 Rubric

每题按四个维度评分，每个维度 0 到 25 分，总分 100 分：

| 维度 | 说明 |
| --- | --- |
| `relevance` | 是否紧扣题目要求 |
| `clarity` | 表达是否清晰易懂 |
| `evidence` | 是否给出具体经历、数据、结果 |
| `structure` | 回答结构是否完整 |

### 9.7 薄弱点抽取规则

- 来源为问答时：
  - 回答失败或证据不足时抽取知识薄弱点
- 来源为搭子时：
  - 从用户主动暴露的困惑或重复困惑中抽取
- 来源为简历诊断时：
  - 从 `missing_keywords` 和 `risky_phrases` 中抽取
- 来源为面试时：
  - 当题目得分低于 60 分时抽取

## 10. 前端页面设计

### 10.1 登录页

核心组件：

- 邮箱输入框
- 密码输入框
- 登录按钮

请求接口：

- `POST /auth/login`

### 10.2 首页 Dashboard

核心组件：

- 场景入口卡片
- 最近资料卡片
- 最近问答卡片
- 薄弱点列表
- 复习任务列表
- AI 学习搭子卡片

请求接口：

- `GET /scenes`
- `GET /documents`
- `GET /memory/weak-points`
- `GET /review/tasks`
- `GET /buddy/profile`

### 10.3 场景工作台页

核心组件：

- 场景头部信息
- 快捷提问区
- 文档入口
- 搭子入口
- 场景专属功能入口

### 10.4 文档中心

核心组件：

- 文件上传区
- JD 文本输入区
- 文档列表
- 文档状态标签

请求接口：

- `POST /documents/upload`
- `POST /documents/jd`
- `GET /documents`

### 10.5 知识问答页

核心组件：

- 提问输入框
- 问答消息列表
- 引用展示区

请求接口：

- `POST /qa/ask`

### 10.6 AI 学习搭子页

核心组件：

- 搭子名字编辑器
- 人设选择器
- 对话区
- 推荐动作区
- 搭子总结卡片

请求接口：

- `GET /buddy/profile`
- `POST /buddy/profile`
- `POST /buddy/chat`

### 10.7 复习页

核心组件：

- 薄弱点列表
- 复习任务列表
- 完成按钮
- 结果选择器

请求接口：

- `GET /memory/weak-points`
- `GET /review/tasks`
- `POST /review/tasks/{id}/complete`

### 10.8 简历诊断页

核心组件：

- 简历选择器
- JD 选择器
- 开始诊断按钮
- 匹配度卡片
- 缺失关键词列表
- 改写建议列表

请求接口：

- `GET /documents`
- `POST /career/resume-diagnosis`

### 10.9 模拟面试页

核心组件：

- JD 选择器
- 创建 Session 按钮
- 题目卡片
- 回答输入框
- 评分反馈区

请求接口：

- `POST /career/interview/sessions`
- `GET /career/interview/sessions/{id}`
- `POST /career/interview/sessions/{id}/answer`

## 11. 配置与环境变量

### 11.1 必需配置

| 配置项 | 说明 |
| --- | --- |
| `MYSQL_HOST` | MySQL 主机 |
| `MYSQL_PORT` | MySQL 端口 |
| `MYSQL_USER` | MySQL 用户名 |
| `MYSQL_PASSWORD` | MySQL 密码 |
| `MYSQL_DATABASE` | MySQL 数据库名 |
| `REDIS_URL` | Redis 连接地址 |
| `CELERY_BROKER_URL` | Celery Broker 地址 |
| `CELERY_RESULT_BACKEND` | Celery 结果存储地址 |
| `OPENAI_API_KEY` | 模型调用密钥 |
| `MODEL_NAME` | 使用的模型名称 |
| `CHROMA_PERSIST_DIR` | Chroma 本地持久化目录 |
| `FILE_STORAGE_DIR` | 上传文件存储目录 |
| `JWT_SECRET` | 登录态签名密钥 |

### 11.2 预留配置

| 配置项 | 说明 |
| --- | --- |
| `FEISHU_APP_ID` | 后续飞书接入预留 |
| `QQ_BOT_TOKEN` | 后续 QQ 接入预留 |

## 12. 开发约束

### 12.1 接口与 Schema 约束

- 统一响应结构必须贯穿全部 API。
- 请求 Schema 与响应 Schema 使用 Pydantic 明确定义。
- ORM Model 与 API Schema 必须分离。

### 12.2 文档处理约束

- 支持的首版文件类型：`pdf`、`txt`、`md`
- 单文件大小建议限制为 `20MB`
- 解析失败必须记录 `error_message`
- 未完成解析的文档不能参与问答、诊断或面试

### 12.3 业务约束

- 所有 API 必须显式携带或推导 `scene_id`
- 搭子对话必须感知当前场景
- 所有引用必须来自当前用户当前场景自己的资料
- `career` 专属能力只能在 `scene_id=career` 下调用

## 13. 测试方案

### 13.1 单元测试

- 文档状态流转测试
- Redis 会话上下文测试
- Celery 文档解析任务测试
- 薄弱点合并与更新测试
- 搭子配置与记忆摘要测试
- 复习时间计算测试

### 13.2 API 集成测试

- 登录接口
- 场景列表接口
- 文档上传与查询接口
- 问答接口
- 搭子配置与聊天接口
- 简历诊断接口
- 模拟面试创建与答题接口
- 复习任务完成接口

### 13.3 主流程 E2E

通用学习路径：

`登录 -> 进入 general -> 上传资料 -> 提问 -> 与搭子互动 -> 查看薄弱点 -> 完成复习任务`

求职场景路径：

`登录 -> 进入 career -> 上传简历 -> 录入 JD -> 执行诊断 -> 创建面试 -> 回答题目 -> 查看薄弱点 -> 完成复习任务`

### 13.4 样例数据准备

- 一份通用学习资料样例
- 一份中文技术岗位简历样例
- 一份后端开发 JD 样例
- 一组搭子提醒样例数据
- 一组模拟面试结果快照数据

## 14. 非功能需求

### 14.1 响应时间目标

- 登录与普通查询接口：`< 1s`
- RAG 问答：`< 5s`
- 搭子对话：`< 6s`
- 简历诊断：`< 10s`
- 单题面试评分：`< 10s`

### 14.2 最小日志埋点

至少记录以下日志：

- 用户登录
- 文档上传
- 文档解析开始与结束
- 问答请求
- 搭子对话请求
- 诊断请求
- 面试答题请求
- 复习任务完成
- Celery 任务执行耗时与异常
- Redis 缓存命中和关键失效

### 14.3 基础安全要求

- 登录态必须校验用户身份
- 上传文件必须校验类型与大小
- 所有查询默认附带当前用户过滤
- 敏感配置通过环境变量注入

### 14.4 数据隔离要求

- MySQL 查询必须基于当前用户和场景过滤
- Chroma 检索必须附带用户和场景维度元数据过滤
- Redis 会话 key 必须带用户和场景前缀

## 15. 后续扩展说明

以下内容不属于首版依赖，但在设计上保留扩展空间：

- 飞书和 QQ 渠道
- 支付和团队版
- 用户自建场景
- 场景广场
- 更重的游戏化体系
