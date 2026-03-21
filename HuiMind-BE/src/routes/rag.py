"""RAG routes."""

from src.data_schemas.api_schemas.base import ApiResponse
from src.data_schemas.api_schemas.rag import AskData
from src.handlers.rag import RagHandler
from src.routes.base import BaseAPIRouter

router = BaseAPIRouter(tags=["问答"])
handler = RagHandler()

router.post(
    "/api/v1/qa/ask",
    handler.ask_question,
    response_model=ApiResponse[AskData],
    summary="知识问答",
)

router.post(
    "/api/v1/qa/ask_stream",
    handler.ask_question_stream,
    summary="知识问答（流式）",
)
