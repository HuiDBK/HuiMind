"""Buddy services."""

from src.dao.orm.manager.buddy import BuddyProfileManager
from src.dao.orm.table import BuddyProfileTable
from src.data_schemas.api_schemas.buddy import BuddyChatData, BuddyChatRequest, BuddyProfileData, BuddyProfileRequest
from src.services.base import DomainSupportService, now_ts


class BuddyService(DomainSupportService):
    async def get_profile(self) -> BuddyProfileData:
        profile = await self.get_buddy_profile_row()
        return self._to_profile_data(profile)

    async def update_profile(self, payload: BuddyProfileRequest) -> BuddyProfileData:
        profile = await self.get_buddy_profile_row()
        await BuddyProfileManager().update(
            values={"name": payload.name, "persona": payload.persona, "last_interaction_at": now_ts()},
            conds=[BuddyProfileTable.id == profile.id],
        )
        updated = await BuddyProfileManager().query_by_id(profile.id)
        return self._to_profile_data(updated)

    async def chat(self, payload: BuddyChatRequest) -> BuddyChatData:
        profile = await self.get_buddy_profile_row()
        memory_summary = (
            f"用户最近在 {payload.scene_id} 场景反复提到“{payload.message[:24]}”，"
            "这说明需要更聚焦的拆解和复习节奏。"
        )
        await BuddyProfileManager().update(
            values={"memory_summary": memory_summary, "last_interaction_at": now_ts()},
            conds=[BuddyProfileTable.id == profile.id],
        )
        return BuddyChatData(
            reply=(
                f"{profile.name}已经收到你的状态，我建议先把这次问题拆成“核心概念、应用场景、易错点”三段来记。"
                "你先说一个最卡住的点，我继续陪你往下掰开。"
            ),
            memory_summary=memory_summary,
            suggested_actions=["查看今日复习任务", "重新提问一次薄弱点", "整理一张 3 点总结卡片"],
        )

    @staticmethod
    def _to_profile_data(profile) -> BuddyProfileData:
        return BuddyProfileData(
            buddy_id=profile.id,
            name=profile.name,
            persona=profile.persona,
            memory_summary=profile.memory_summary,
            last_interaction_at=profile.last_interaction_at,
        )
