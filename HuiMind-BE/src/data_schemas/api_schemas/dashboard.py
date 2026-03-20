"""Dashboard API schemas."""

from pydantic import BaseModel

from src.data_schemas.api_schemas.base import SceneID


class DashboardCard(BaseModel):
    title: str
    subtitle: str


class DashboardData(BaseModel):
    current_scene_id: SceneID
    quick_actions: list[str]
    cards: list[DashboardCard]
