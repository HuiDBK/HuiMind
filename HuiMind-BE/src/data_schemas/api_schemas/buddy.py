"""Buddy API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.data_schemas.api_schemas.base import BuddyPersona, SceneID


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
