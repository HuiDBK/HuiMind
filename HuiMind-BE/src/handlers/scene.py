"""Scene handlers."""

from src.handlers.base import BaseHandler
from src.services.scene import SceneService


class SceneHandler(BaseHandler):
    def __init__(self):
        self.service = SceneService()

    async def list_scenes(self):
        data_list = await self.service.list_scenes()
        return self.page(total=len(data_list), data_list=data_list)
