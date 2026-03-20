"""Scene API schemas."""

from src.data_schemas.api_schemas.base import OrmSchema, SceneID


class SceneItem(OrmSchema):
    scene_id: SceneID
    name: str
    description: str
    enabled_tools: list[str]
