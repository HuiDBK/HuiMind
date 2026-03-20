"""Dashboard handlers."""

from src.handlers.base import BaseHandler
from src.services.dashboard import DashboardService


class DashboardHandler(BaseHandler):
    def __init__(self):
        self.service = DashboardService()

    async def get_dashboard(self):
        return self.success(await self.service.get_dashboard())
