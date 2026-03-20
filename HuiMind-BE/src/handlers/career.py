"""Career handlers."""

from fastapi import Path

from src.data_schemas.api_schemas.career import InterviewAnswerRequest, InterviewSessionCreateRequest, ResumeDiagnosisRequest
from src.handlers.base import BaseHandler
from src.services.career import CareerService


class CareerHandler(BaseHandler):
    def __init__(self):
        self.service = CareerService()

    async def resume_diagnosis(self, payload: ResumeDiagnosisRequest):
        return self.success(await self.service.resume_diagnosis(payload))

    async def create_interview_session(self, payload: InterviewSessionCreateRequest):
        return self.success(await self.service.create_interview_session(payload))

    async def get_interview_session(self, session_id: int = Path(..., description="面试会话 ID")):
        return self.success(await self.service.get_interview_session(session_id))

    async def answer_interview_question(self, payload: InterviewAnswerRequest, session_id: int = Path(..., description="面试会话 ID")):
        return self.success(await self.service.answer_interview_question(session_id, payload))
