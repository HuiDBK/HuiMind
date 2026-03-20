"""Document handlers."""

from fastapi import Query

from src.data_schemas.api_schemas.document import DocumentUploadRequest, JDCreateRequest
from src.handlers.base import BaseHandler
from src.services.document import DocumentService


class DocumentHandler(BaseHandler):
    def __init__(self):
        self.service = DocumentService()

    async def upload_document(self, payload: DocumentUploadRequest):
        return self.success(await self.service.upload_document(payload))

    async def create_jd(self, payload: JDCreateRequest):
        return self.success(await self.service.create_jd(payload))

    async def list_documents(
        self,
        scene_id: str | None = Query(default=None, description="场景 ID"),
        doc_type: str | None = Query(default=None, description="资料类型"),
        status_value: str | None = Query(default=None, alias="status", description="资料状态"),
    ):
        data_list = await self.service.list_documents(scene_id=scene_id, doc_type=doc_type, status_value=status_value)
        return self.page(total=len(data_list), data_list=data_list)
