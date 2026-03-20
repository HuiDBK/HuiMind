"""Shared API schemas."""

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")
ItemT = TypeVar("ItemT")

SceneID = Literal["general", "career"]
DocType = Literal["resume", "jd", "material", "note"]
BuddyPersona = Literal["gentle", "strict", "energetic", "calm"]
ReviewResult = Literal["mastered", "review_again"]
InterviewMode = Literal["standard", "pressure"]


class OrmSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PageData(BaseModel, Generic[ItemT]):
    total: int = Field(description="总数量")
    data_list: list[ItemT] = Field(default_factory=list, description="列表数据")


class ApiResponse(BaseModel, Generic[T]):
    code: int = Field(default=0, description="业务状态码，0 表示成功")
    message: str = Field(default="ok", description="响应消息")
    data: T
