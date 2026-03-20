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
        if not user or user.password != payload.password:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误")
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
