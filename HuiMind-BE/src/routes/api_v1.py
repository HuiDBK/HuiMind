"""API v1 mock routes."""

from fastapi import APIRouter, Path

from src.data_schemas.api_schemas.v1 import (
    ApiResponse,
    AskData,
    AskRequest,
    BuddyChatData,
    BuddyChatRequest,
    BuddyProfileData,
    BuddyProfileRequest,
    DashboardData,
    DocumentCreateData,
    DocumentListData,
    DocumentUploadRequest,
    InterviewAnswerData,
    InterviewAnswerRequest,
    InterviewSessionCreateData,
    InterviewSessionCreateRequest,
    InterviewSessionDetailData,
    JDCreateRequest,
    LoginData,
    LoginRequest,
    MeData,
    ResumeDiagnosisData,
    ResumeDiagnosisRequest,
    ReviewTaskCompleteData,
    ReviewTaskCompleteRequest,
    ReviewTaskListData,
    SceneListData,
    WeakPointListData,
)
from src.services.mock_data import (
    build_ask_data,
    build_buddy_chat_data,
    build_buddy_profile_data,
    build_dashboard_data,
    build_document_create_data,
    build_document_list_data,
    build_interview_answer_data,
    build_interview_session_create_data,
    build_interview_session_detail_data,
    build_login_data,
    build_me_data,
    build_resume_diagnosis_data,
    build_review_task_complete_data,
    build_review_task_list_data,
    build_scene_list_data,
    build_weak_point_list_data,
)

router = APIRouter()


@router.get("", response_model=ApiResponse[dict], tags=["系统"])
def root() -> ApiResponse[dict]:
    return ApiResponse(data={"service": "HuiMind API", "version": "v1", "docs": "/docs"})


@router.get("/health", response_model=ApiResponse[dict], tags=["系统"], summary="健康检查")
def health() -> ApiResponse[dict]:
    return ApiResponse(data={"status": "ok"})


@router.post("/auth/login", response_model=ApiResponse[LoginData], tags=["认证"], summary="用户登录")
def login(payload: LoginRequest) -> ApiResponse[LoginData]:
    return ApiResponse(data=build_login_data(payload))


@router.get("/me", response_model=ApiResponse[MeData], tags=["认证"], summary="当前用户信息")
def me() -> ApiResponse[MeData]:
    return ApiResponse(data=build_me_data())


@router.get("/dashboard", response_model=ApiResponse[DashboardData], tags=["首页"], summary="首页概览")
def dashboard() -> ApiResponse[DashboardData]:
    return ApiResponse(data=build_dashboard_data())


@router.get("/scenes", response_model=ApiResponse[SceneListData], tags=["场景"], summary="场景列表")
def scenes() -> ApiResponse[SceneListData]:
    return ApiResponse(data=build_scene_list_data())


@router.post(
    "/documents/upload",
    response_model=ApiResponse[DocumentCreateData],
    tags=["资料"],
    summary="模拟上传资料",
    description="当前阶段使用 JSON 模拟上传元数据，后续接入真实文件上传能力。",
)
def upload_document(payload: DocumentUploadRequest) -> ApiResponse[DocumentCreateData]:
    return ApiResponse(data=build_document_create_data(payload.scene_id, payload.doc_type, payload.filename))


@router.post("/documents/jd", response_model=ApiResponse[DocumentCreateData], tags=["资料"], summary="录入 JD")
def create_jd(payload: JDCreateRequest) -> ApiResponse[DocumentCreateData]:
    return ApiResponse(data=build_document_create_data(payload.scene_id, "jd", payload.title))


@router.get("/documents", response_model=ApiResponse[DocumentListData], tags=["资料"], summary="文档列表")
def list_documents(scene_id: str | None = None, doc_type: str | None = None, status: str | None = None) -> ApiResponse[DocumentListData]:
    return ApiResponse(data=build_document_list_data(scene_id=scene_id, doc_type=doc_type, status=status))


@router.post("/qa/ask", response_model=ApiResponse[AskData], tags=["问答"], summary="知识问答")
def ask_question(payload: AskRequest) -> ApiResponse[AskData]:
    return ApiResponse(data=build_ask_data(payload))


@router.get("/buddy/profile", response_model=ApiResponse[BuddyProfileData], tags=["学习搭子"], summary="获取搭子配置")
def get_buddy_profile() -> ApiResponse[BuddyProfileData]:
    return ApiResponse(data=build_buddy_profile_data())


@router.post("/buddy/profile", response_model=ApiResponse[BuddyProfileData], tags=["学习搭子"], summary="更新搭子配置")
def update_buddy_profile(payload: BuddyProfileRequest) -> ApiResponse[BuddyProfileData]:
    return ApiResponse(data=build_buddy_profile_data(name=payload.name, persona=payload.persona))


@router.post("/buddy/chat", response_model=ApiResponse[BuddyChatData], tags=["学习搭子"], summary="搭子对话")
def chat_with_buddy(payload: BuddyChatRequest) -> ApiResponse[BuddyChatData]:
    return ApiResponse(data=build_buddy_chat_data(payload))


@router.get("/memory/weak-points", response_model=ApiResponse[WeakPointListData], tags=["记忆"], summary="薄弱点列表")
def list_weak_points(scene_id: str | None = None) -> ApiResponse[WeakPointListData]:
    return ApiResponse(data=build_weak_point_list_data(scene_id=scene_id))


@router.get("/review/tasks", response_model=ApiResponse[ReviewTaskListData], tags=["复习"], summary="复习任务列表")
def list_review_tasks(scene_id: str | None = None, status: str | None = None) -> ApiResponse[ReviewTaskListData]:
    return ApiResponse(data=build_review_task_list_data(scene_id=scene_id, status=status))


@router.post(
    "/review/tasks/{task_id}/complete",
    response_model=ApiResponse[ReviewTaskCompleteData],
    tags=["复习"],
    summary="完成复习任务",
)
def complete_review_task(
    payload: ReviewTaskCompleteRequest,
    task_id: int = Path(..., description="复习任务 ID"),
) -> ApiResponse[ReviewTaskCompleteData]:
    return ApiResponse(data=build_review_task_complete_data(task_id=task_id, result=payload.result))


@router.post(
    "/career/resume-diagnosis",
    response_model=ApiResponse[ResumeDiagnosisData],
    tags=["Career"],
    summary="简历诊断",
)
def resume_diagnosis(payload: ResumeDiagnosisRequest) -> ApiResponse[ResumeDiagnosisData]:
    return ApiResponse(data=build_resume_diagnosis_data(payload))


@router.post(
    "/career/interview/sessions",
    response_model=ApiResponse[InterviewSessionCreateData],
    tags=["Career"],
    summary="创建模拟面试",
)
def create_interview_session(payload: InterviewSessionCreateRequest) -> ApiResponse[InterviewSessionCreateData]:
    return ApiResponse(data=build_interview_session_create_data(payload))


@router.get(
    "/career/interview/sessions/{session_id}",
    response_model=ApiResponse[InterviewSessionDetailData],
    tags=["Career"],
    summary="模拟面试详情",
)
def get_interview_session(session_id: int = Path(..., description="面试会话 ID")) -> ApiResponse[InterviewSessionDetailData]:
    return ApiResponse(data=build_interview_session_detail_data(session_id))


@router.post(
    "/career/interview/sessions/{session_id}/answer",
    response_model=ApiResponse[InterviewAnswerData],
    tags=["Career"],
    summary="提交面试回答",
)
def answer_interview_question(
    payload: InterviewAnswerRequest,
    session_id: int = Path(..., description="面试会话 ID"),
) -> ApiResponse[InterviewAnswerData]:
    return ApiResponse(data=build_interview_answer_data(session_id=session_id, payload=payload))
