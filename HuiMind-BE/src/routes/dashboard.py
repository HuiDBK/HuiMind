"""Dashboard routes."""

from src.data_schemas.api_schemas.base import ApiResponse
from src.data_schemas.api_schemas.dashboard import DashboardData
from src.handlers.dashboard import DashboardHandler
from src.routes.base import BaseAPIRouter

router = BaseAPIRouter(tags=["dashboard"])
handler = DashboardHandler()

router.get(
    "/api/v1/dashboard",
    handler.get_dashboard,
    response_model=ApiResponse[DashboardData],
    summary="首页概览",
)
