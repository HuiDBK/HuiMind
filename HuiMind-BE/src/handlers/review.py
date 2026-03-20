"""Review handlers."""

from fastapi import Path, Query

from src.data_schemas.api_schemas.review import ReviewTaskCompleteRequest
from src.handlers.base import BaseHandler
from src.services.review import ReviewService


class ReviewHandler(BaseHandler):
    def __init__(self):
        self.service = ReviewService()

    async def list_weak_points(self, scene_id: str | None = Query(default=None, description="场景 ID")):
        data_list = await self.service.list_weak_points(scene_id=scene_id)
        return self.page(total=len(data_list), data_list=data_list)

    async def list_review_tasks(
        self,
        scene_id: str | None = Query(default=None, description="场景 ID"),
        status_value: str | None = Query(default=None, alias="status", description="任务状态"),
    ):
        data_list = await self.service.list_review_tasks(scene_id=scene_id, status_value=status_value)
        return self.page(total=len(data_list), data_list=data_list)

    async def complete_review_task(self, payload: ReviewTaskCompleteRequest, task_id: int = Path(..., description="复习任务 ID")):
        return self.success(await self.service.complete_review_task(task_id=task_id, result=payload.result))
