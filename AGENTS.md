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
