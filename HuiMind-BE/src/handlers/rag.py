"""RAG handlers."""

from src.data_schemas.api_schemas.rag import AskRequest
from src.handlers.base import BaseHandler
from src.services.rag import RagService


class RagHandler(BaseHandler):
    def __init__(self):
        self.service = RagService()

    async def ask_question(self, payload: AskRequest):
        return self.success(await self.service.ask_question(payload))
