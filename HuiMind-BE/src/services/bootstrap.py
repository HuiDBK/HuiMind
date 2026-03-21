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
        base_system_prompt = "你是 HuiMind AI 伴学助手。你需要基于用户上传的资料进行回答，回答必须尽量附带引用来源；资料不足时要明确说明并给出下一步建议。"
        for payload in [
            {
                "scene_id": "general",
                "name": "通用学习",
                "description": "面向日常自学和资料沉淀的默认学习空间。",
                "enabled_tools": ["search_knowledge", "generate_quiz", "update_weakness", "schedule_review"],
                "system_prompt": base_system_prompt,
                "skill_prompt": "优先引导用户上传资料并建立可检索的知识库；回答时以概念梳理 + 可执行练习为主。",
                "eval_rubric": {},
            },
            {
                "scene_id": "career",
                "name": "求职助手",
                "description": "围绕简历诊断和模拟面试构建的首发官方场景。",
                "enabled_tools": ["search_knowledge", "rubric_evaluate", "generate_quiz", "update_weakness", "schedule_review"],
                "system_prompt": base_system_prompt,
                "skill_prompt": "回答更偏实战：可量化表达、STAR 结构、面试官追问；必要时先问澄清问题再给建议。",
                "eval_rubric": {"type": "STAR", "dimensions": ["situation", "task", "action", "result"]},
            },
            {
                "scene_id": "kaoyan",
                "name": "考研备考",
                "description": "围绕真题与错题归纳的备考场景。",
                "enabled_tools": ["search_knowledge", "generate_quiz", "update_weakness", "schedule_review"],
                "system_prompt": base_system_prompt,
                "skill_prompt": "偏应试：题型拆解、真题规律、错因归因与复习节奏。",
                "eval_rubric": {},
            },
            {
                "scene_id": "gongkao",
                "name": "考公备考",
                "description": "围绕申论批改与行测练习的备考场景。",
                "enabled_tools": ["search_knowledge", "rubric_evaluate", "generate_quiz", "update_weakness", "schedule_review"],
                "system_prompt": base_system_prompt,
                "skill_prompt": "申论更重结构与表达，行测更重解题路径；必要时建议联网补充时政。",
                "eval_rubric": {"type": "essay", "dimensions": ["结构", "立意", "论证", "表达", "规范"]},
            },
        ]:
            await SceneManager().add(payload)

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
