"""Document API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.data_schemas.api_schemas.base import DocType, OrmSchema, SceneID


class DocumentUploadRequest(BaseModel):
    scene_id: SceneID
    doc_type: DocType
    file_id: int = Field(examples=[1])
    oss_key: str = Field(examples=["user/1/20260322/abc123.pdf"])


class JDCreateRequest(BaseModel):
    scene_id: SceneID = Field(default="career")
    title: str = Field(examples=["后端开发工程师"])
    content: str | None = Field(default=None, examples=["负责 API 设计、MySQL 建模和 Redis 缓存优化"])
    source_url: str | None = Field(default=None, examples=["https://jobs.example.com/backend"])


class DocumentCreateData(BaseModel):
    document_id: int
    scene_id: SceneID
    doc_type: str
    filename: str
    status: str
    file_id: int | None = None
    oss_key: str | None = None


class DocumentItem(OrmSchema):
    id: int
    scene_id: SceneID
    doc_type: DocType
    filename: str
    status: str
    summary: str
    created_at: datetime
