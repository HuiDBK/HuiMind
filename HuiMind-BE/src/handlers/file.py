"""File handlers."""

from fastapi import File, Form, UploadFile

from src.data_schemas.api_schemas.base import SceneID
from src.handlers.base import BaseHandler
from src.services.file import FileService


class FileHandler(BaseHandler):
    def __init__(self):
        self.service = FileService()

    async def upload(self, file: UploadFile = File(...), scene_id: SceneID | None = Form(default=None)):
        return self.success(await self.service.upload(file=file, scene_id=scene_id))

