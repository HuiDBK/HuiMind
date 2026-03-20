"""Buddy routes."""

from src.data_schemas.api_schemas.base import ApiResponse
from src.data_schemas.api_schemas.buddy import BuddyChatData, BuddyProfileData
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

router.post(
    "/api/v1/buddy/chat",
    handler.chat,
    response_model=ApiResponse[BuddyChatData],
    summary="搭子对话",
)
