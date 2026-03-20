"""Buddy handlers."""

from src.data_schemas.api_schemas.buddy import BuddyChatRequest, BuddyProfileRequest
from src.handlers.base import BaseHandler
from src.services.buddy import BuddyService


class BuddyHandler(BaseHandler):
    def __init__(self):
        self.service = BuddyService()

    async def get_profile(self):
        return self.success(await self.service.get_profile())

    async def update_profile(self, payload: BuddyProfileRequest):
        return self.success(await self.service.update_profile(payload))

    async def chat(self, payload: BuddyChatRequest):
        return self.success(await self.service.chat(payload))
