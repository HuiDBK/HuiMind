"""Bootstrap services."""

from datetime import timedelta

from sqlalchemy import func

from src.dao.orm.manager.auth import UserManager
from src.dao.orm.manager.buddy import BuddyProfileManager
from src.dao.orm.manager.document import DocumentManager
from src.dao.orm.manager.review import ReviewTaskManager, WeakPointManager
from src.dao.orm.manager.scene import SceneManager
from src.services.base import BaseService, DEFAULT_USER_EMAIL, now_ts


class BootstrapService(BaseService):
    async def seed_initial_data(self) -> None:
        await self._seed_scenes()
        await self._seed_users()
        await self._seed_documents()
        await self._seed_buddy_profile()
        await self._seed_weak_points()
        await self._seed_review_tasks()

    async def _seed_scenes(self) -> None:
        count = await SceneManager().query_one(cols=[func.count()], flat=True) or 0
        if count:
            return
        for payload in [
            {
                "scene_id": "general",
                "name": "通用学习",
                "description": "面向日常自学和资料沉淀的默认学习空间。",
                "enabled_tools": ["qa", "quiz", "update_weakness", "query_memory", "schedule"],
                "system_prompt": (
                    "## 你的角色定位\n"
                    "你是 HuiMind 的通用学习搭子，目标是让用户把学习资料沉淀成可检索的知识库，并在日常自学中持续进步。\n\n"
                    "## 核心打法\n"
                    "1. 资料优先：用户提出知识性问题时，优先基于用户上传资料回答，并尽量给出引用来源。\n"
                    "2. 资料不足：当资料中没有相关内容时，明确告知“不足以得出结论”，并给出下一步（引导上传/补充关键词/建议搜索方向）。\n"
                    "3. 学习导向：回答以“概念梳理 + 例子 + 可执行练习/自测题”组织，优先输出可操作步骤。\n"
                    "4. 连续感：结尾用一句引导问题把对话推进到下一步（例如要不要出题、要不要加入复习）。\n\n"
                    "## 边界与禁区\n"
                    "- 不要编造资料里不存在的事实；不确定就说明不确定。\n"
                    "- 面向学习任务，不做无关闲聊的长篇输出（闲聊可简短回应）。"
                ),
                "rag_policy": {"k": 6, "use_rewrite": False, "use_rerank": False, "use_compression": False},
                "eval_rubric": {},
            },
            {
                "scene_id": "career",
                "name": "求职助手",
                "description": "围绕简历诊断和模拟面试构建的首发官方场景。",
                "enabled_tools": ["qa", "rubric_eval", "quiz", "update_weakness", "query_memory", "schedule"],
                "system_prompt": (
                    "## 你的角色定位\n"
                    "你是 HuiMind 的求职助手，站在“面试官 + 资深求职教练”的视角，帮助用户提升简历、项目表达与面试表现。\n\n"
                    "## 核心打法\n"
                    "1. 实战优先：建议必须可落地，优先给可直接替换到简历里的措辞与结构。\n"
                    "2. 量化与证据：引导用户用数据、结果与可验证证据表达影响力，避免空话套话。\n"
                    "3. STAR/结构化：项目经历、面试回答尽量按 STAR（或问题-思路-行动-结果）组织。\n"
                    "4. 追问式澄清：信息不足时先问 1-3 个关键澄清问题再给结论；必要时给两套方案（保守/进攻）。\n\n"
                    "## 边界与禁区\n"
                    "- 不要虚构项目经历或编造数据；需要时提示用户如何真实量化。\n"
                    "- 不要输出冗长理论，优先输出模板 + 示例 + 可执行修改清单。"
                ),
                "rag_policy": {"k": 6, "use_rewrite": False, "use_rerank": False, "use_compression": False},
                "eval_rubric": {"type": "STAR", "dimensions": ["situation", "task", "action", "result"]},
            },
            {
                "scene_id": "kaoyan",
                "name": "考研备考",
                "description": "围绕真题与错题归纳的备考场景。",
                "enabled_tools": ["qa", "quiz", "update_weakness", "query_memory", "schedule"],
                "system_prompt": (
                    "## 你的角色定位\n"
                    "你是 HuiMind 的考研备考搭子，目标是帮助用户用“真题驱动 + 错因归因 + 复习节奏”拿分。\n\n"
                    "## 核心打法\n"
                    "1. 题型拆解：优先把问题归类到题型/考点，给出标准解题路径与易错点。\n"
                    "2. 错因归因：对错题要给出“错在哪里/为什么错/如何避免再错”的归因与针对性练习。\n"
                    "3. 以练促学：讲完就给 1-3 道小题或变式题，巩固迁移。\n"
                    "4. 复习节奏：对高频易错点建议加入复习计划，提醒间隔复习。\n\n"
                    "## 边界与禁区\n"
                    "- 不要脱离用户资料与真题乱讲；资料不足时提示用户补充题干/章节/截图。\n"
                    "- 输出尽量结构化（步骤/要点/公式/结论），少空泛鼓励。"
                ),
                "rag_policy": {"k": 6, "use_rewrite": False, "use_rerank": False, "use_compression": False},
                "eval_rubric": {},
            },
            {
                "scene_id": "gongkao",
                "name": "考公备考",
                "description": "围绕申论批改与行测练习的备考场景。",
                "enabled_tools": ["qa", "rubric_eval", "quiz", "update_weakness", "query_memory", "schedule"],
                "system_prompt": (
                    "## 你的角色定位\n"
                    "你是 HuiMind 的考公备考搭子，覆盖申论与行测两类任务：申论重结构表达与立意论证，行测重解题路径与速度。\n\n"
                    "## 核心打法\n"
                    "1. 申论：先给结构框架（分论点/论证链路/素材落点），再给可直接替换的表达与修改建议。\n"
                    "2. 行测：给“最短可复用的解题路径”（题型识别→方法→关键步骤→易错点→时间控制）。\n"
                    "3. 素材与时政：资料不足时优先引导用户上传本地资料；需要最新信息时提示补充来源或上传材料。\n"
                    "4. 应试输出：优先输出模板、要点清单与练习建议，帮助用户快速提分。\n\n"
                    "## 边界与禁区\n"
                    "- 不要编造政策条文或时政事实；不确定就说明需要资料/来源。\n"
                    "- 批改与建议要具体可执行，避免泛泛而谈。"
                ),
                "rag_policy": {"k": 6, "use_rewrite": False, "use_rerank": False, "use_compression": False},
                "eval_rubric": {"type": "essay", "dimensions": ["结构", "立意", "论证", "表达", "规范"]},
            },
        ]:
            await SceneManager().bulk_add([payload])

    async def _seed_users(self) -> None:
        count = await UserManager().query_one(cols=[func.count()], flat=True) or 0
        if count:
            return
        await UserManager().add({"username": "HuiMind 用户", "password": "123456", "phone": "", "email": DEFAULT_USER_EMAIL})

    async def _seed_documents(self) -> None:
        count = await DocumentManager().query_one(cols=[func.count()], flat=True) or 0
        if count:
            return
        for payload in [
            {"scene_id": "general", "doc_type": "note", "filename": "redis-learning-notes.md", "status": "ready", "summary": "Redis 基础概念、常见数据结构和缓存策略摘要。", "content": "Redis 数据结构、缓存击穿、缓存穿透、缓存雪崩、过期策略。"},
            {"scene_id": "career", "doc_type": "resume", "filename": "backend-resume.pdf", "status": "ready", "summary": "后端开发岗位简历，包含 FastAPI、MySQL、Redis 项目经历。", "content": "FastAPI MySQL Redis API 设计 性能优化 项目经历。"},
            {"scene_id": "career", "doc_type": "jd", "filename": "后端开发工程师 JD", "status": "ready", "summary": "偏 Python 后端方向，关注 API 设计、数据库与缓存能力。", "content": "Python FastAPI MySQL Redis 高并发 监控体系。"},
        ]:
            await DocumentManager().add(payload)

    async def _seed_buddy_profile(self) -> None:
        count = await BuddyProfileManager().query_one(cols=[func.count()], flat=True) or 0
        if count:
            return
        user = await UserManager().query_one(orders=[UserManager.orm_table.id.asc()])
        await BuddyProfileManager().add(
            {"user_id": user.id if user else 1, "name": "小智", "persona": "gentle", "memory_summary": "你最近主要在学习 Redis 和系统设计，同时在准备后端岗位简历。", "last_interaction_at": now_ts() - timedelta(hours=3)}
        )

    async def _seed_weak_points(self) -> None:
        count = await WeakPointManager().query_one(cols=[func.count()], flat=True) or 0
        if count:
            return
        for payload in [
            {"scene_id": "general", "concept": "Redis 缓存穿透与击穿的区别", "source_type": "qa", "wrong_count": 2, "correct_rate": 50.0, "mastery_level": "reviewing", "next_review_at": now_ts() + timedelta(hours=6)},
            {"scene_id": "career", "concept": "项目成果量化表达", "source_type": "diagnosis", "wrong_count": 1, "correct_rate": 60.0, "mastery_level": "weak", "next_review_at": now_ts() + timedelta(days=1)},
        ]:
            await WeakPointManager().add(payload)

    async def _seed_review_tasks(self) -> None:
        count = await ReviewTaskManager().query_one(cols=[func.count()], flat=True) or 0
        if count:
            return
        for payload in [
            {"scene_id": "general", "concept": "Redis 缓存穿透与击穿的区别", "due_at": now_ts() + timedelta(hours=6), "status": "pending"},
            {"scene_id": "career", "concept": "项目成果量化表达", "due_at": now_ts() + timedelta(days=1), "status": "pending"},
        ]:
            await ReviewTaskManager().add(payload)
