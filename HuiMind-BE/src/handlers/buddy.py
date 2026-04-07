"""Buddy handlers.

AI 学习搭子配置处理器。
注意：搭子对话已合并到智能问答接口，通过 Agent 的人格层实现。
"""

from src.data_schemas.api_schemas.buddy import BuddyProfileRequest
from src.handlers.base import BaseHandler
from src.services.buddy import BuddyService


class BuddyHandler(BaseHandler):
    """搭子配置处理器。"""

    def __init__(self):
        self.service = BuddyService()

    async def get_profile(self):
        """获取搭子配置。"""
        return self.success(await self.service.get_profile())

    async def update_profile(self, payload: BuddyProfileRequest):
        """更新搭子配置。"""
        return self.success(await self.service.update_profile(payload))
