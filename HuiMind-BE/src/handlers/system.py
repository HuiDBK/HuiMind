"""System handlers."""

from src.handlers.base import BaseHandler
from src.services.system import SystemService


class SystemHandler(BaseHandler):
    def __init__(self):
        self.service = SystemService()

    async def root(self):
        return self.success(await self.service.root())

    async def health(self):
        return self.success(await self.service.health())
