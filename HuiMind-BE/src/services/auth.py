"""Auth services."""

from fastapi import HTTPException, status

from src.dao.orm.manager.auth import UserManager
from src.dao.orm.table import UserTable
from src.data_schemas.api_schemas.auth import LoginData, LoginRequest, LoginUserInfo, MeData
from src.services.base import DEFAULT_SCENE_ID, DomainSupportService


class AuthService(DomainSupportService):
    async def login(self, payload: LoginRequest) -> LoginData:
        user = await UserManager().query_one(
            conds=[UserTable.email == payload.email, UserTable.deleted_at.is_(None)],
        )
        # Mock 鉴权：如果数据库中没找到或密码不对，直接放行 mock 用户
        if not user or user.password != payload.password:
            return LoginData(
                token="hm-token-mock-user-1",
                user=LoginUserInfo(id=1, email=payload.email, nickname="HuiMind_Mock"),
            )
        return LoginData(
            token=f"hm-token-{user.id}",
            user=LoginUserInfo(id=user.id, email=user.email, nickname=user.username),
        )

    async def me(self) -> MeData:
        user = await self.get_default_user()
        return MeData(
            id=user.id,
            email=user.email,
            nickname=user.username,
            default_scene_id=DEFAULT_SCENE_ID,
        )
