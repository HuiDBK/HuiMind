"""Pydantic schemas for API v1 mock routes."""

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

SceneID = Literal["general", "career"]
DocType = Literal["resume", "jd", "material", "note"]
BuddyPersona = Literal["gentle", "strict", "energetic", "calm"]
ReviewResult = Literal["mastered", "review_again"]


class ApiResponse(BaseModel, Generic[T]):
    code: int = Field(default=0, description="业务状态码，0 表示成功")
    message: str = Field(default="ok", description="响应消息")
    data: T


class LoginRequest(BaseModel):
    email: str = Field(examples=["demo@huimind.ai"])
    password: str = Field(min_length=6, examples=["123456"])


class UserInfo(BaseModel):
    id: int
    email: str
    nickname: str


class LoginData(BaseModel):
    token: str
    user: UserInfo


class MeData(UserInfo):
    default_scene_id: SceneID


class SceneItem(BaseModel):
    scene_id: SceneID
    name: str
    description: str
    enabled_tools: list[str]


class SceneListData(BaseModel):
    items: list[SceneItem]


class DashboardCard(BaseModel):
    title: str
    subtitle: str


class DashboardData(BaseModel):
    current_scene_id: SceneID
    quick_actions: list[str]
    cards: list[DashboardCard]


class DocumentUploadRequest(BaseModel):
    scene_id: SceneID
    doc_type: Literal["resume", "material", "note"]
    filename: str = Field(examples=["system-design-notes.pdf"])
    source_url: str | None = Field(default=None, examples=["https://example.com/article"])


class JDCreateRequest(BaseModel):
    scene_id: Literal["career"]
    title: str = Field(examples=["后端开发工程师"])
    content: str | None = Field(default=None, examples=["负责 API 设计、MySQL 建模和 Redis 缓存优化"])
    source_url: str | None = Field(default=None, examples=["https://jobs.example.com/backend"])


class DocumentCreateData(BaseModel):
    document_id: int
    scene_id: SceneID
    doc_type: str
    filename: str
    status: str


class DocumentItem(BaseModel):
    id: int
    scene_id: SceneID
    doc_type: DocType
    filename: str
    status: str
    summary: str
    created_at: datetime


class DocumentListData(BaseModel):
    items: list[DocumentItem]


class AskRequest(BaseModel):
    scene_id: SceneID
    session_id: int | None = Field(default=1)
    question: str = Field(examples=["请根据我的资料总结本章重点"])


class CitationItem(BaseModel):
    document_id: int
    source_label: str
    source_locator: str
    quote: str


class AskData(BaseModel):
    session_id: int
    answer: str
    citations: list[CitationItem]
    insufficient_context: bool


class BuddyProfileRequest(BaseModel):
    name: str = Field(examples=["小智"])
    persona: BuddyPersona = Field(examples=["gentle"])


class BuddyProfileData(BaseModel):
    buddy_id: int
    name: str
    persona: BuddyPersona
    memory_summary: str
    last_interaction_at: datetime | None


class BuddyChatRequest(BaseModel):
    scene_id: SceneID
    message: str = Field(examples=["我这两天总记不住 Redis 的核心概念，你帮我梳理一下"])


class BuddyChatData(BaseModel):
    reply: str
    memory_summary: str
    suggested_actions: list[str]


class WeakPointItem(BaseModel):
    id: int
    scene_id: SceneID
    concept: str
    source_type: str
    wrong_count: int
    correct_rate: float
    mastery_level: str
    next_review_at: datetime


class WeakPointListData(BaseModel):
    items: list[WeakPointItem]


class ReviewTaskItem(BaseModel):
    id: int
    scene_id: SceneID
    concept: str
    due_at: datetime
    status: str


class ReviewTaskListData(BaseModel):
    items: list[ReviewTaskItem]


class ReviewTaskCompleteRequest(BaseModel):
    result: ReviewResult


class ReviewTaskCompleteData(BaseModel):
    task_id: int
    status: str
    next_review_at: datetime


class ResumeDiagnosisRequest(BaseModel):
    scene_id: Literal["career"]
    resume_doc_id: int
    jd_doc_id: int


class RiskyPhraseItem(BaseModel):
    original: str
    reason: str


class RewriteSuggestionItem(BaseModel):
    original: str
    rewritten: str


class ResumeDiagnosisData(BaseModel):
    diagnosis_id: int
    match_score: float
    matched_keywords: list[str]
    missing_keywords: list[str]
    risky_phrases: list[RiskyPhraseItem]
    rewrite_suggestions: list[RewriteSuggestionItem]
    summary: str


class InterviewSessionCreateRequest(BaseModel):
    scene_id: Literal["career"]
    jd_doc_id: int
    mode: Literal["standard", "pressure"] = Field(default="standard")


class InterviewQuestionItem(BaseModel):
    turn_id: int
    question_order: int
    question: str


class InterviewSessionCreateData(BaseModel):
    session_id: int
    status: str
    questions: list[InterviewQuestionItem]


class InterviewTurnDetail(BaseModel):
    turn_id: int
    question_order: int
    question: str
    answer: str | None
    score: float | None


class InterviewSessionDetailData(BaseModel):
    id: int
    scene_id: Literal["career"]
    status: str
    overall_score: float
    summary: str
    turns: list[InterviewTurnDetail]


class InterviewAnswerRequest(BaseModel):
    turn_id: int
    answer: str = Field(examples=["我会先澄清业务目标，然后拆解数据链路和缓存策略"])


class InterviewFeedback(BaseModel):
    relevance: int
    clarity: int
    evidence: int
    structure: int
    comment: str


class InterviewAnswerData(BaseModel):
    session_id: int
    turn_id: int
    score: float
    feedback: InterviewFeedback
    weak_points: list[str]
    session_status: str
