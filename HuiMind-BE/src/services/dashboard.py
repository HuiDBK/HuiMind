"""Dashboard services."""

from sqlalchemy import func

from src.dao.orm.manager.buddy import BuddyProfileManager
from src.dao.orm.manager.document import DocumentManager
from src.dao.orm.manager.review import ReviewTaskManager
from src.dao.orm.table import BuddyProfileTable, DocumentTable, ReviewTaskTable
from src.data_schemas.api_schemas.dashboard import DashboardCard, DashboardData
from src.services.base import BaseService, DEFAULT_SCENE_ID


class DashboardService(BaseService):
    async def get_dashboard(self) -> DashboardData:
        document_count = (
            await DocumentManager().query_one(cols=[func.count()], conds=[DocumentTable.deleted_at.is_(None)], flat=True)
            or 0
        )
        pending_review_count = (
            await ReviewTaskManager().query_one(
                cols=[func.count()],
                conds=[ReviewTaskTable.status == "pending", ReviewTaskTable.deleted_at.is_(None)],
                flat=True,
            )
            or 0
        )
        buddy = await BuddyProfileManager().query_one(
            conds=[BuddyProfileTable.deleted_at.is_(None)],
            orders=[BuddyProfileTable.id.asc()],
        )
        return DashboardData(
            current_scene_id=DEFAULT_SCENE_ID,
            quick_actions=["上传资料", "开始提问", "和搭子聊聊", "查看复习任务"],
            cards=[
                DashboardCard(title="最近资料", subtitle=f"已上传 {document_count} 份学习资料"),
                DashboardCard(title="待复习任务", subtitle=f"当前有 {pending_review_count} 个待处理复习点"),
                DashboardCard(title="AI 学习搭子", subtitle=f"{buddy.name if buddy else '学习搭子'}正在跟进你的学习状态"),
            ],
        )
