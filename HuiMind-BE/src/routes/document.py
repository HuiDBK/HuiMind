"""Document routes."""

from src.data_schemas.api_schemas.base import ApiResponse, PageData
from src.data_schemas.api_schemas.document import DocumentCreateData, DocumentItem
from src.handlers.document import DocumentHandler
from src.routes.base import BaseAPIRouter

router = BaseAPIRouter(tags=["资料"])
handler = DocumentHandler()

router.post(
    "/api/v1/documents/upload",
    handler.upload_document,
    response_model=ApiResponse[DocumentCreateData],
    summary="上传资料元数据",
)

router.post(
    "/api/v1/documents/jd",
    handler.create_jd,
    response_model=ApiResponse[DocumentCreateData],
    summary="录入 JD",
)

router.get(
    "/api/v1/documents",
    handler.list_documents,
    response_model=ApiResponse[PageData[DocumentItem]],
    summary="文档列表",
)
