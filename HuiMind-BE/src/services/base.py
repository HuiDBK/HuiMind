"""Base service definitions and shared helpers."""

from datetime import datetime, timedelta

from fastapi import HTTPException, status

from src.dao.orm.manager.auth import UserManager
from src.dao.orm.manager.buddy import BuddyProfileManager
from src.dao.orm.manager.document import DocumentManager
from src.dao.orm.manager.review import ReviewTaskManager, WeakPointManager
from src.dao.orm.table import BuddyProfileTable, DocumentTable, ReviewTaskTable, UserTable, WeakPointTable

DEFAULT_SCENE_ID = "general"
DEFAULT_USER_EMAIL = "demo@huimind.ai"


def now_ts() -> datetime:
    return datetime.now().replace(microsecond=0)


class BaseService:
    pass


class DomainSupportService(BaseService):
    async def get_default_user(self) -> UserTable:
        user = await UserManager().query_one(
            conds=[UserTable.deleted_at.is_(None)],
            orders=[UserTable.id.asc()],
        )
        if not user:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="缺少默认用户数据")
        return user

    async def get_buddy_profile_row(self) -> BuddyProfileTable:
        profile = await BuddyProfileManager().query_one(
            conds=[BuddyProfileTable.deleted_at.is_(None)],
            orders=[BuddyProfileTable.id.asc()],
        )
        if not profile:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="缺少学习搭子配置")
        return profile

    async def get_document_or_404(self, document_id: int) -> DocumentTable:
        document = await DocumentManager().query_by_id(document_id)
        if not document or document.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料不存在")
        return document

    async def get_review_task_or_404(self, task_id: int) -> ReviewTaskTable:
        task = await ReviewTaskManager().query_by_id(task_id)
        if not task or task.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="复习任务不存在")
        return task

    async def upsert_weak_point(
        self,
        *,
        scene_id: str,
        concept: str,
        source_type: str,
        mastery_level: str,
    ) -> None:
        row = await WeakPointManager().query_one(
            conds=[WeakPointTable.scene_id == scene_id, WeakPointTable.concept == concept, WeakPointTable.deleted_at.is_(None)]
        )
        if row:
            await WeakPointManager().update(
                values={
                    "wrong_count": row.wrong_count + 1,
                    "mastery_level": mastery_level,
                    "next_review_at": now_ts() + timedelta(days=1),
                },
                conds=[WeakPointTable.id == row.id],
            )
            return
        await WeakPointManager().add(
            {
                "scene_id": scene_id,
                "concept": concept,
                "source_type": source_type,
                "wrong_count": 1,
                "correct_rate": 50.0,
                "mastery_level": mastery_level,
                "next_review_at": now_ts() + timedelta(days=1),
            }
        )

    @staticmethod
    def extract_keywords(raw_text: str) -> list[str]:
        candidates = ["Python", "FastAPI", "MySQL", "Redis", "高并发", "监控体系", "API 设计", "性能优化"]
        text = raw_text.lower()
        return [item for item in candidates if item.lower() in text]

    @staticmethod
    def build_document_summary(doc_type: str, filename: str) -> str:
        return f"{doc_type.upper()} 资料《{filename}》已入库，可用于问答、复习和场景分析。"

    @staticmethod
    def build_interview_questions(mode: str) -> list[str]:
        questions = [
            "请介绍一个你最有代表性的后端项目。",
            "如果核心接口出现高延迟，你会怎么排查？",
            "你在项目里如何平衡数据库和缓存设计？",
        ]
        if mode == "pressure":
            questions[1] = "线上核心接口 P99 飙高，你只能先做一件事，你会怎么选？"
        return questions

    @classmethod
    def score_answer(cls, answer: str) -> float:
        length_bonus = min(len(answer) / 8, 18)
        keyword_bonus = len(cls.extract_keywords(answer)) * 6
        return round(min(95.0, 52.0 + length_bonus + keyword_bonus), 1)

    @staticmethod
    def build_interview_feedback(answer: str, score: float):
        from src.data_schemas.api_schemas.career import InterviewFeedback

        has_metric = any(token in answer for token in ["%", "毫秒", "ms", "QPS", "提升", "降低"])
        return InterviewFeedback(
            relevance=min(10, max(6, int(score // 10))),
            clarity=8 if len(answer) >= 30 else 6,
            evidence=8 if has_metric else 6,
            structure=8 if "先" in answer or "然后" in answer else 6,
            comment="回答方向是对的，再补具体场景、指标和结果，会更像真实面试里的高分答案。",
        )
