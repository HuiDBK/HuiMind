"""Review routes."""

from src.data_schemas.api_schemas.base import ApiResponse, PageData
from src.data_schemas.api_schemas.review import ReviewTaskCompleteData, ReviewTaskItem, WeakPointItem
from src.handlers.review import ReviewHandler
from src.routes.base import BaseAPIRouter

router = BaseAPIRouter()
handler = ReviewHandler()

router.get(
    "/api/v1/memory/weak-points",
    handler.list_weak_points,
    response_model=ApiResponse[PageData[WeakPointItem]],
    tags=["记忆"],
    summary="薄弱点列表",
)

router.get(
    "/api/v1/review/tasks",
    handler.list_review_tasks,
    response_model=ApiResponse[PageData[ReviewTaskItem]],
    tags=["复习"],
    summary="复习任务列表",
)

router.post(
    "/api/v1/review/tasks/{task_id}/complete",
    handler.complete_review_task,
    response_model=ApiResponse[ReviewTaskCompleteData],
    tags=["复习"],
    summary="完成复习任务",
)
