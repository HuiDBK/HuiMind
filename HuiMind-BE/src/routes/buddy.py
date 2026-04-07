"""Buddy routes.

AI 学习搭子配置接口。
注意：搭子对话已合并到智能问答接口，通过 Agent 的人格层实现。
"""

from src.data_schemas.api_schemas.base import ApiResponse
from src.data_schemas.api_schemas.buddy import BuddyProfileData
from src.handlers.buddy import BuddyHandler
from src.routes.base import BaseAPIRouter

router = BaseAPIRouter(tags=["学习搭子"])
handler = BuddyHandler()

router.get(
    "/api/v1/buddy/profile",
    handler.get_profile,
    response_model=ApiResponse[BuddyProfileData],
    summary="获取搭子配置",
)

router.post(
    "/api/v1/buddy/profile",
    handler.update_profile,
    response_model=ApiResponse[BuddyProfileData],
    summary="更新搭子配置",
)
