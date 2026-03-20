"""Career API schemas."""

from pydantic import BaseModel, Field

from src.data_schemas.api_schemas.base import InterviewMode, SceneID


class ResumeDiagnosisRequest(BaseModel):
    scene_id: SceneID = Field(default="career")
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
    scene_id: SceneID = Field(default="career")
    jd_doc_id: int
    mode: InterviewMode = Field(default="standard")


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
    scene_id: SceneID
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
