"""System routes."""

from src.data_schemas.api_schemas.base import ApiResponse
from src.handlers.system import SystemHandler
from src.routes.base import BaseAPIRouter

router = BaseAPIRouter(tags=["系统"])
handler = SystemHandler()

router.get(
    "/api/v1/",
    handler.root,
    response_model=ApiResponse[dict],
)

router.get(
    "/api/v1/health",
    handler.health,
    response_model=ApiResponse[dict],
    summary="健康检查",
)
