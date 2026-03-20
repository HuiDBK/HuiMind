"""Scene routes."""

from src.data_schemas.api_schemas.base import ApiResponse, PageData
from src.data_schemas.api_schemas.scene import SceneItem
from src.handlers.scene import SceneHandler
from src.routes.base import BaseAPIRouter

router = BaseAPIRouter()
handler = SceneHandler()

router.get(
    "/api/v1/scenes",
    handler.list_scenes,
    response_model=ApiResponse[PageData[SceneItem]],
    tags=["场景"],
    summary="场景列表",
)
