"""Review API schemas."""

from datetime import datetime

from pydantic import BaseModel

from src.data_schemas.api_schemas.base import OrmSchema, ReviewResult, SceneID


class WeakPointItem(OrmSchema):
    id: int
    scene_id: SceneID
    concept: str
    source_type: str
    wrong_count: int
    correct_rate: float
    mastery_level: str
    next_review_at: datetime


class ReviewTaskItem(OrmSchema):
    id: int
    scene_id: SceneID
    concept: str
    due_at: datetime
    status: str


class ReviewTaskCompleteRequest(BaseModel):
    result: ReviewResult


class ReviewTaskCompleteData(BaseModel):
    task_id: int
    status: str
    next_review_at: datetime
