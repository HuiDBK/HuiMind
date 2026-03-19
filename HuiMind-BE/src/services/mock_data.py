"""Mock data builders for the API documentation phase."""

from datetime import datetime, timedelta

from src.data_schemas.api_schemas.v1 import (
    AskData,
    AskRequest,
    BuddyChatData,
    BuddyChatRequest,
    BuddyProfileData,
    DashboardCard,
    DashboardData,
    DocumentCreateData,
    DocumentItem,
    DocumentListData,
    InterviewAnswerData,
    InterviewAnswerRequest,
    InterviewFeedback,
    InterviewQuestionItem,
    InterviewSessionCreateData,
    InterviewSessionCreateRequest,
    InterviewSessionDetailData,
    InterviewTurnDetail,
    LoginData,
    LoginRequest,
    MeData,
    ResumeDiagnosisData,
    ResumeDiagnosisRequest,
    ReviewTaskCompleteData,
    ReviewTaskListData,
    ReviewTaskItem,
    RiskyPhraseItem,
    RewriteSuggestionItem,
    SceneItem,
    SceneListData,
    UserInfo,
    WeakPointItem,
    WeakPointListData,
    CitationItem,
)


def _now() -> datetime:
    return datetime.now().replace(microsecond=0)


def build_login_data(payload: LoginRequest) -> LoginData:
    return LoginData(
        token="mock-jwt-token",
        user=UserInfo(id=1001, email=payload.email, nickname="HuiMind 用户"),
    )


def build_me_data() -> MeData:
    return MeData(id=1001, email="demo@huimind.ai", nickname="HuiMind 用户", default_scene_id="general")


def build_dashboard_data() -> DashboardData:
    return DashboardData(
        current_scene_id="general",
        quick_actions=["上传资料", "开始提问", "和搭子聊聊", "查看复习任务"],
        cards=[
            DashboardCard(title="最近资料", subtitle="已上传 3 份学习资料"),
            DashboardCard(title="待复习任务", subtitle="今天有 2 个到期复习点"),
            DashboardCard(title="AI 学习搭子", subtitle="小智已经连续陪你学习 4 天"),
        ],
    )


def build_scene_list_data() -> SceneListData:
    return SceneListData(
        items=[
            SceneItem(
                scene_id="general",
                name="通用学习",
                description="面向日常自学和资料沉淀的默认学习空间。",
                enabled_tools=["documents", "qa", "memory_review", "buddy"],
            ),
            SceneItem(
                scene_id="career",
                name="求职助手",
                description="围绕简历诊断和模拟面试构建的首发官方场景。",
                enabled_tools=["documents", "qa", "memory_review", "buddy", "resume_diagnosis", "interview"],
            ),
        ]
    )


def build_document_create_data(scene_id: str, doc_type: str, filename: str) -> DocumentCreateData:
    return DocumentCreateData(
        document_id=2001,
        scene_id=scene_id,
        doc_type=doc_type,
        filename=filename,
        status="uploaded",
    )


def build_document_list_data(scene_id: str | None = None, doc_type: str | None = None, status: str | None = None) -> DocumentListData:
    items = [
        DocumentItem(
            id=2001,
            scene_id="general",
            doc_type="note",
            filename="redis-learning-notes.md",
            status="ready",
            summary="Redis 基础概念、常见数据结构和缓存策略摘要。",
            created_at=_now() - timedelta(days=2),
        ),
        DocumentItem(
            id=2002,
            scene_id="career",
            doc_type="resume",
            filename="backend-resume.pdf",
            status="ready",
            summary="后端开发岗位简历，包含 FastAPI、MySQL、Redis 项目经历。",
            created_at=_now() - timedelta(days=1),
        ),
        DocumentItem(
            id=2003,
            scene_id="career",
            doc_type="jd",
            filename="后端开发工程师 JD",
            status="ready",
            summary="偏 Python 后端方向，关注 API 设计、数据库与缓存能力。",
            created_at=_now(),
        ),
    ]
    if scene_id:
        items = [item for item in items if item.scene_id == scene_id]
    if doc_type:
        items = [item for item in items if item.doc_type == doc_type]
    if status:
        items = [item for item in items if item.status == status]
    return DocumentListData(items=items)


def build_ask_data(payload: AskRequest) -> AskData:
    answer = (
        "根据你当前上传的资料，这部分重点可以先抓住 Redis 的数据结构、过期策略和缓存穿透防护，"
        "再结合你项目里的缓存落地经验去理解。"
    )
    return AskData(
        session_id=payload.session_id or 1,
        answer=answer,
        citations=[
            CitationItem(
                document_id=2001,
                source_label="redis-learning-notes.md",
                source_locator="chunk-2",
                quote="Redis 常见面试重点包括数据结构、缓存雪崩、穿透和击穿。",
            )
        ],
        insufficient_context=False,
    )


def build_buddy_profile_data(name: str = "小智", persona: str = "gentle") -> BuddyProfileData:
    return BuddyProfileData(
        buddy_id=3001,
        name=name,
        persona=persona,
        memory_summary="你最近主要在学习 Redis 和系统设计，同时在准备后端岗位简历。",
        last_interaction_at=_now() - timedelta(hours=3),
    )


def build_buddy_chat_data(payload: BuddyChatRequest) -> BuddyChatData:
    return BuddyChatData(
        reply=(
            f"我看到你现在在 `{payload.scene_id}` 场景学习，这次我们先把最容易混淆的点拆开。"
            "你先记住核心概念，再做一轮针对性复习，我会继续帮你盯着。"
        ),
        memory_summary="用户最近反复提到 Redis 和缓存策略，说明这部分还不够稳。",
        suggested_actions=["查看今日复习任务", "重新提问一次薄弱点", "整理一张 3 点总结卡片"],
    )


def build_weak_point_list_data(scene_id: str | None = None) -> WeakPointListData:
    items = [
        WeakPointItem(
            id=4001,
            scene_id="general",
            concept="Redis 缓存穿透与击穿的区别",
            source_type="qa",
            wrong_count=2,
            correct_rate=50.0,
            mastery_level="reviewing",
            next_review_at=_now() + timedelta(hours=6),
        ),
        WeakPointItem(
            id=4002,
            scene_id="career",
            concept="项目成果量化表达",
            source_type="diagnosis",
            wrong_count=1,
            correct_rate=60.0,
            mastery_level="weak",
            next_review_at=_now() + timedelta(days=1),
        ),
    ]
    if scene_id:
        items = [item for item in items if item.scene_id == scene_id]
    return WeakPointListData(items=items)


def build_review_task_list_data(scene_id: str | None = None, status: str | None = None) -> ReviewTaskListData:
    items = [
        ReviewTaskItem(
            id=5001,
            scene_id="general",
            concept="Redis 缓存穿透与击穿的区别",
            due_at=_now() + timedelta(hours=6),
            status="pending",
        ),
        ReviewTaskItem(
            id=5002,
            scene_id="career",
            concept="项目成果量化表达",
            due_at=_now() + timedelta(days=1),
            status="pending",
        ),
    ]
    if scene_id:
        items = [item for item in items if item.scene_id == scene_id]
    if status:
        items = [item for item in items if item.status == status]
    return ReviewTaskListData(items=items)


def build_review_task_complete_data(task_id: int, result: str) -> ReviewTaskCompleteData:
    delta = timedelta(days=3 if result == "mastered" else 1)
    return ReviewTaskCompleteData(task_id=task_id, status="completed", next_review_at=_now() + delta)


def build_resume_diagnosis_data(_: ResumeDiagnosisRequest) -> ResumeDiagnosisData:
    return ResumeDiagnosisData(
        diagnosis_id=6001,
        match_score=78.5,
        matched_keywords=["Python", "FastAPI", "MySQL", "Redis"],
        missing_keywords=["高并发", "监控体系"],
        risky_phrases=[
            RiskyPhraseItem(
                original="负责一些后端开发工作",
                reason="表达泛化，没有体现具体动作和结果。",
            )
        ],
        rewrite_suggestions=[
            RewriteSuggestionItem(
                original="负责一些后端开发工作",
                rewritten="负责 FastAPI 后端接口开发与 MySQL 数据建模，支撑核心业务模块上线。",
            )
        ],
        summary="你的技术栈与目标 JD 比较接近，但项目成果量化和高并发表达还需要加强。",
    )


def build_interview_session_create_data(payload: InterviewSessionCreateRequest) -> InterviewSessionCreateData:
    questions = [
        InterviewQuestionItem(turn_id=7001, question_order=1, question="请介绍一个你最有代表性的后端项目。"),
        InterviewQuestionItem(turn_id=7002, question_order=2, question="你在项目里是如何使用 Redis 提升性能的？"),
        InterviewQuestionItem(turn_id=7003, question_order=3, question="如果线上接口响应变慢，你会如何排查？"),
    ]
    return InterviewSessionCreateData(session_id=7100 + payload.jd_doc_id, status="in_progress", questions=questions)


def build_interview_session_detail_data(session_id: int) -> InterviewSessionDetailData:
    return InterviewSessionDetailData(
        id=session_id,
        scene_id="career",
        status="in_progress",
        overall_score=82.0,
        summary="你的回答结构比较清晰，但还可以增加量化结果和故障排查细节。",
        turns=[
            InterviewTurnDetail(
                turn_id=7001,
                question_order=1,
                question="请介绍一个你最有代表性的后端项目。",
                answer="我参与过一个中后台系统重构项目，负责 API 和缓存模块。",
                score=84.0,
            ),
            InterviewTurnDetail(
                turn_id=7002,
                question_order=2,
                question="你在项目里是如何使用 Redis 提升性能的？",
                answer=None,
                score=None,
            ),
        ],
    )


def build_interview_answer_data(session_id: int, payload: InterviewAnswerRequest) -> InterviewAnswerData:
    return InterviewAnswerData(
        session_id=session_id,
        turn_id=payload.turn_id,
        score=81.0,
        feedback=InterviewFeedback(
            relevance=22,
            clarity=21,
            evidence=18,
            structure=20,
            comment="回答方向是对的，但还缺少量化结果和具体排查细节。",
        ),
        weak_points=["项目成果量化表达", "线上问题排查步骤"],
        session_status="in_progress",
    )
