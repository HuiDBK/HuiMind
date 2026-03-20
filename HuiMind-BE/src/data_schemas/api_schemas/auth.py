"""Auth API schemas."""

from pydantic import BaseModel, Field

from src.data_schemas.api_schemas.base import OrmSchema, SceneID


class LoginRequest(BaseModel):
    email: str = Field(examples=["demo@huimind.ai"])
    password: str = Field(min_length=6, examples=["123456"])


class LoginUserInfo(OrmSchema):
    id: int
    email: str
    nickname: str


class UserInfo(OrmSchema):
    id: int
    email: str
    nickname: str
    default_scene_id: SceneID


class LoginData(BaseModel):
    token: str
    user: LoginUserInfo


class MeData(UserInfo):
    pass
