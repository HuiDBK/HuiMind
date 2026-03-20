"""Auth routes."""

from src.data_schemas.api_schemas.auth import LoginData, MeData
from src.data_schemas.api_schemas.base import ApiResponse
from src.handlers.auth import AuthHandler
from src.routes.base import BaseAPIRouter

router = BaseAPIRouter(tags=["认证"])
handler = AuthHandler()

router.post("/api/v1/auth/login", handler.login, response_model=ApiResponse[LoginData], summary="用户登录")
router.get("/api/v1/me", handler.me, response_model=ApiResponse[MeData], summary="当前用户信息")
