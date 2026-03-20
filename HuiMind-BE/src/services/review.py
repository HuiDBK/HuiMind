"""Review services."""

from datetime import timedelta

from src.dao.orm.manager.review import ReviewTaskManager, WeakPointManager
from src.dao.orm.table import ReviewTaskTable, WeakPointTable
from src.data_schemas.api_schemas.review import ReviewTaskCompleteData, ReviewTaskItem, WeakPointItem
from src.services.base import DomainSupportService, now_ts


class ReviewService(DomainSupportService):
    async def list_weak_points(self, *, scene_id: str | None = None) -> list[WeakPointItem]:
        conds = [WeakPointTable.deleted_at.is_(None)]
        if scene_id:
            conds.append(WeakPointTable.scene_id == scene_id)
        rows = await WeakPointManager().query_all(
            conds=conds,
            orders=[WeakPointTable.next_review_at.asc(), WeakPointTable.id.asc()],
        )
        return [WeakPointItem.model_validate(row) for row in rows]

    async def list_review_tasks(self, *, scene_id: str | None = None, status_value: str | None = None) -> list[ReviewTaskItem]:
        conds = [ReviewTaskTable.deleted_at.is_(None)]
        if scene_id:
            conds.append(ReviewTaskTable.scene_id == scene_id)
        if status_value:
            conds.append(ReviewTaskTable.status == status_value)
        rows = await ReviewTaskManager().query_all(
            conds=conds,
            orders=[ReviewTaskTable.due_at.asc(), ReviewTaskTable.id.asc()],
        )
        return [ReviewTaskItem.model_validate(row) for row in rows]

    async def complete_review_task(self, task_id: int, result: str) -> ReviewTaskCompleteData:
        await self.get_review_task_or_404(task_id)
        next_review_at = now_ts() + timedelta(days=3 if result == "mastered" else 1)
        await ReviewTaskManager().update(
            values={"status": "completed", "due_at": next_review_at},
            conds=[ReviewTaskTable.id == task_id],
        )
        return ReviewTaskCompleteData(task_id=task_id, status="completed", next_review_at=next_review_at)
