"""Auth handlers."""

from src.data_schemas.api_schemas.auth import LoginRequest
from src.handlers.base import BaseHandler
from src.services.auth import AuthService


class AuthHandler(BaseHandler):
    def __init__(self):
        self.service = AuthService()

    async def login(self, payload: LoginRequest):
        return self.success(await self.service.login(payload))

    async def me(self):
        return self.success(await self.service.me())
