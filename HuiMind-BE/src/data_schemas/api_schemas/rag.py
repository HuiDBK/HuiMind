"""RAG API schemas."""

from pydantic import BaseModel, Field

from src.data_schemas.api_schemas.base import SceneID


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
