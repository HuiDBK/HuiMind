"""RAG handlers."""

import json

from fastapi.responses import StreamingResponse

from src.data_schemas.api_schemas.rag import AskRequest
from src.handlers.base import BaseHandler
from src.services.agent import AgentService


class RagHandler(BaseHandler):
    def __init__(self):
        self.service = AgentService()

    async def ask_question(self, payload: AskRequest):
        return self.success(await self.service.ask(payload))

    async def ask_question_stream(self, payload: AskRequest):
        async def event_gen():
            async for ev in self.service.ask_stream(payload):
                yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"

        return StreamingResponse(
            event_gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
