# HuiMind

## README 摘要

HuiMind-AI 伴学平台

### 产品概述

AI 伴学平台是一款面向个人用户的 AI 驱动学习助手，核心差异化是「有记忆、会追踪、能主动推送、有趣到停不下来」。用户上传自己的学习资料，平台提供智能问答、练习出题、薄弱点追踪、艾宾浩斯复习调度，并通过飞书/QQ 机器人在碎片时间触达用户。

产品采用「统一 Agent 引擎 + 场景配置层」架构，MVP 内置三个官方场景（求职助手、考研备考、考公备考），同时提供通用学习底座和用户自建场景能力。平台收集用户行为数据，驱动官方场景持续迭代，这是产品的数据飞轮。

## 顶层目录说明

- `HuiMind-FE`: 前端项目，当前是 Next.js 应用，包含 `app/`、`components/`、`hooks/`、`lib/` 等目录。
- `HuiMind-BE`: 后端项目，当前是 Python 服务端，包含 `src/` 主代码、`tests/` 测试、`main.py` 启动入口等。
- `docs`: 项目文档目录，包含 MVP 规划、技术设计和产品文档。
- `res`: 设计资源与原型资料目录，包含不同场景和页面的设计稿资源。
- `README.md`: 项目总览与产品简介。
- `LICENSE`: 开源许可证文件。
- `ruff.toml`: Python 相关代码风格/检查配置。
- `.pre-commit-config.yaml`: 提交前检查配置。
- `.codex`: Codex 相关本地配置目录。

## 使用建议

- 进入项目后，优先根据当前任务判断是在 `HuiMind-FE` 还是 `HuiMind-BE` 中工作。
- 需要理解产品目标、MVP 范围或业务背景时，先阅读 `README.md` 和 `docs/` 下的文档。

## 后端开发规范

- 后端 `routes` 层只负责路由注册，必须继承 `BaseAPIRouter`，不要在该层编写具体业务逻辑。
- 后端路由注册统一使用 `router.get(...)`、`router.post(...)`、`router.put(...)`、`router.delete(...)` 这类方式，不使用 `class XxxRouter.__init__` 中逐条注册的风格作为默认方案。
- 后端路由注册统一使用多行写法，并优先直接写完整可检索路径，例如：
  ```python
  router.post(
      "/api/v1/xxx",
      XxxHandler.some_method,
      response_model=SomeRespModel,
      summary="xxx",
  )
  ```
- 后端 `handlers` 层负责参数校验、调用 `service`，并在最后统一组织返回参数，必须继承 `BaseHandler`。
- 后端 `service` 层负责具体业务逻辑处理，必须继承 `BaseService`。
- 后端 `manager` 层负责数据库查询与数据访问操作，必须继承 `BaseManager`。
- 后端代码需要按业务模块分别建目录和文件，例如按 `auth`、`scene`、`document`、`career` 等模块拆分；不要把多个业务模块集中写在同一个文件或同一个通用业务目录里。
- 后端接口响应格式必须统一为 `code`、`message`、`data` 三层结构。
- 当接口返回普通对象时，响应格式为 `{"code": ..., "message": "...", "data": {...}}`。
- 当接口返回分页列表时，`data` 必须固定为 `{"total": ..., "data_list": [...]}`，不要使用其他分页字段命名。

## 语言环境规范

- 项目所有文档、代码注释、TODO 以及与 AI 助手的交互应优先使用 **中文**。
- 前端页面文案应保持一致的中文风格，确保符合中文语境下的用户体验。

## 代码注释规范

目标：让任何新同学在不阅读全部上下文的情况下，也能快速理解代码意图、关键约束与边界条件。

### 总体要求（强制）

- 所有复杂函数、复杂类、关键业务流程必须有详细注释（docstring/JSDoc + 必要的行内解释）。
- 注释必须准确、清晰、可验证：描述“为什么这么做、关键约束是什么、失败时会怎样”，而不是复述代码字面含义。
- 注释与实现必须同步更新；发现注释过期视为缺陷必须修复。
- 禁止在注释中泄露任何密钥、Token、用户隐私、生产地址等敏感信息。

### Python 注释标准（强制：Google Python Style Guide）

范围：后端所有 Python 模块（尤其是 `routes/handlers/services/managers/tasks/utils`）。

- 模块级注释：每个模块必须有模块 docstring，说明该模块职责、边界与对外行为。
- 类 docstring：所有业务类、基类、对外可复用类必须有类 docstring，说明用途、关键字段/状态、线程/协程安全性（如有）。
- 函数/方法 docstring：所有复杂函数、对外可调用函数、公共方法必须有 docstring，并遵循 Google 样式字段：
  - `Args:` 参数含义、单位/格式、约束、默认值语义。
  - `Returns:` 返回值结构与语义（必要时描述字段含义）。
  - `Raises:` 明确可能抛出的异常类型与触发条件（例如 `HTTPException`、自定义业务异常）。
  - 如适用可补充：`Yields:`、`Attributes:`、`Examples:`、`Note:`。
- 对于关键业务流程（例如：上传→入库→异步切分→向量化→检索→问答），必须在入口函数的 docstring 中写清楚流程步骤与关键决策点。

Google 样式示例（参考模板）：

```python
"""文档入库异步任务。

该模块负责：根据文档元数据读取文件 → 解析/切分 → 写入向量库 → 更新文档状态。
"""


class DocumentParserService:
    """文档解析与入库服务。

负责将用户上传的文件解析为可检索的 chunk，并写入向量库以支持 RAG。
"""

    async def parse_and_index(self, document_id: int) -> bool:
        """解析并入库指定文档。

        Args:
            document_id: 文档 ID（数据库主键）。

        Returns:
            是否成功完成入库（成功写入向量库且状态更新为 ready 返回 True）。

        Raises:
            ValueError: 当 document_id 不存在或数据不完整时抛出。
            RuntimeError: 当向量库写入失败且无法回退时抛出。
        """
        ...
```

### 前端注释标准（强制：JSDoc/TSDoc 风格）

范围：所有前端代码（JavaScript/TypeScript/React/Vue 等）。

- 模块级注释：复杂页面/组件/模块必须在文件顶部说明“该模块解决什么问题、关键交互/状态、与后端接口契约要点”。
- 函数/组件注释：复杂函数、核心 Hook、非直观的 UI 逻辑必须补充 JSDoc/TSDoc：
  - `@param` 参数说明（含格式/约束/默认行为）。
  - `@returns` 返回值说明（含结构语义）。
  - `@throws`（如存在抛错或显式 reject）。
  - `@example`（对外可复用的函数/Hook 推荐提供）。
- 复杂业务逻辑必须有“原因解释型”注释：说明为什么要这样处理（例如：重试策略、幂等键、并发控制、SSE 断线重连、缓存失效等）。

JSDoc/TSDoc 示例（参考模板）：

```ts
/**
 * 建立问答 SSE 连接并按事件类型增量更新 UI。
 *
 * @param payload - 问答请求参数（scene_id/session_id/question）。
 * @returns 可用于中断连接的 abort 函数。
 */
export function startAskStream(payload: AskRequest): () => void {
  // 这里需要显式处理断线与重连，否则用户会看到“回答中断”
  // ...
}
```

### 何时必须写“详细注释”

- 跨模块/跨进程流程：例如 Celery 异步任务、SSE 流式、向量库写入、Redis 会话历史。
- 易错逻辑：并发、幂等、重试、超时、限流、权限校验、数据一致性。
- 业务规则密集：评分规则、场景策略、工具选择、状态机流转。
- 任何未来 2 周内你自己可能也会忘记原因的实现。
