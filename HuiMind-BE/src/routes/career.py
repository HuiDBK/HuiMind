"""Career routes."""

from src.data_schemas.api_schemas.base import ApiResponse
from src.data_schemas.api_schemas.career import InterviewAnswerData, InterviewSessionCreateData, InterviewSessionDetailData, ResumeDiagnosisData
from src.handlers.career import CareerHandler
from src.routes.base import BaseAPIRouter

router = BaseAPIRouter(tags=["Career"])
handler = CareerHandler()

router.post(
    "/api/v1/career/resume-diagnosis",
    handler.resume_diagnosis,
    response_model=ApiResponse[ResumeDiagnosisData],
    summary="简历诊断",
)

router.post(
    "/api/v1/career/interview/sessions",
    handler.create_interview_session,
    response_model=ApiResponse[InterviewSessionCreateData],
    summary="创建模拟面试",
)

router.get(
    "/api/v1/career/interview/sessions/{session_id}",
    handler.get_interview_session,
    response_model=ApiResponse[InterviewSessionDetailData],
    summary="模拟面试详情",
)

router.post(
    "/api/v1/career/interview/sessions/{session_id}/answer",
    handler.answer_interview_question,
    response_model=ApiResponse[InterviewAnswerData],
    summary="提交面试回答",
)
