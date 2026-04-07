"""Buddy services.

AI 学习搭子配置服务，提供：
- 人设配置（名字、风格）
- 记忆摘要管理

注意：搭子对话已合并到智能问答接口，通过 Agent 的人格层实现。
"""

from loguru import logger

from src.dao.orm.manager.buddy import BuddyProfileManager
from src.dao.orm.table import BuddyProfileTable
from src.data_schemas.api_schemas.buddy import BuddyProfileData, BuddyProfileRequest
from src.services.base import DomainSupportService, now_ts


class BuddyService(DomainSupportService):
    """AI 学习搭子配置服务。

    提供搭子人设配置能力，对话能力已合并到 Agent。
    """

    async def get_profile(self) -> BuddyProfileData:
        """获取搭子配置。"""
        profile = await self.get_buddy_profile_row()
        return self._to_profile_data(profile)

    async def update_profile(self, payload: BuddyProfileRequest) -> BuddyProfileData:
        """更新搭子配置。

        Args:
            payload: 配置请求，包含 name 和 persona。

        Returns:
            更新后的配置数据。
        """
        profile = await self.get_buddy_profile_row()
        await BuddyProfileManager().update(
            values={"name": payload.name, "persona": payload.persona, "last_interaction_at": now_ts()},
            conds=[BuddyProfileTable.id == profile.id],
        )
        updated = await BuddyProfileManager().query_by_id(profile.id)
        logger.info(f"[BuddyService] profile updated: name={payload.name} persona={payload.persona}")
        return self._to_profile_data(updated)

    @staticmethod
    def _to_profile_data(profile) -> BuddyProfileData:
        return BuddyProfileData(
            buddy_id=profile.id,
            name=profile.name,
            persona=profile.persona,
            memory_summary=profile.memory_summary,
            last_interaction_at=profile.last_interaction_at,
        )
