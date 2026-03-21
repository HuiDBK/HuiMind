"""File API schemas."""

from pydantic import BaseModel, Field

from src.data_schemas.api_schemas.base import SceneID


class FileUploadData(BaseModel):
    file_id: int
    oss_key: str
    filename: str
    content_type: str
    size_bytes: int
    scene_id: SceneID | None = Field(default=None)

