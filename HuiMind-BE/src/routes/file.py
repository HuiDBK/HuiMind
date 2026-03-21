"""File routes."""

from src.data_schemas.api_schemas.base import ApiResponse
from src.data_schemas.api_schemas.file import FileUploadData
from src.handlers.file import FileHandler
from src.routes.base import BaseAPIRouter

router = BaseAPIRouter(tags=["文件"])
handler = FileHandler()

router.post(
    "/api/v1/files/upload",
    handler.upload,
    response_model=ApiResponse[FileUploadData],
    summary="通用文件上传",
)

