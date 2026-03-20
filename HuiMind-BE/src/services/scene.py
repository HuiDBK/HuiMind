"""Scene services."""

from src.dao.orm.manager.scene import SceneManager
from src.dao.orm.table import SceneTable
from src.data_schemas.api_schemas.scene import SceneItem
from src.services.base import BaseService


class SceneService(BaseService):
    async def list_scenes(self) -> list[SceneItem]:
        rows = await SceneManager().query_all(
            conds=[SceneTable.deleted_at.is_(None)],
            orders=[SceneTable.id.asc()],
        )
        return [
            SceneItem(
                scene_id=row.scene_id,
                name=row.name,
                description=row.description,
                enabled_tools=row.enabled_tools or [],
            )
            for row in rows
        ]
