"""Document services."""

from src.dao.orm.manager.document import DocumentManager
from src.dao.orm.table import DocumentTable
from src.data_schemas.api_schemas.document import DocumentCreateData, DocumentItem, DocumentUploadRequest, JDCreateRequest
from src.services.base import DomainSupportService


class DocumentService(DomainSupportService):
    async def upload_document(self, payload: DocumentUploadRequest) -> DocumentCreateData:
        document_id = await DocumentManager().add(
            {
                "scene_id": payload.scene_id,
                "doc_type": payload.doc_type,
                "filename": payload.filename,
                "status": "ready",
                "summary": self.build_document_summary(payload.doc_type, payload.filename),
                "source_url": payload.source_url,
            }
        )
        document = await DocumentManager().query_by_id(document_id)
        return DocumentCreateData(
            document_id=document.id,
            scene_id=document.scene_id,
            doc_type=document.doc_type,
            filename=document.filename,
            status=document.status,
        )

    async def create_jd(self, payload: JDCreateRequest) -> DocumentCreateData:
        document_id = await DocumentManager().add(
            {
                "scene_id": payload.scene_id,
                "doc_type": "jd",
                "filename": payload.title,
                "status": "ready",
                "summary": "岗位 JD，后续将用于简历诊断和模拟面试。",
                "source_url": payload.source_url,
                "content": payload.content,
            }
        )
        document = await DocumentManager().query_by_id(document_id)
        return DocumentCreateData(
            document_id=document.id,
            scene_id=document.scene_id,
            doc_type=document.doc_type,
            filename=document.filename,
            status=document.status,
        )

    async def list_documents(self, *, scene_id: str | None = None, doc_type: str | None = None, status_value: str | None = None) -> list[DocumentItem]:
        conds = [DocumentTable.deleted_at.is_(None)]
        if scene_id:
            conds.append(DocumentTable.scene_id == scene_id)
        if doc_type:
            conds.append(DocumentTable.doc_type == doc_type)
        if status_value:
            conds.append(DocumentTable.status == status_value)
        rows = await DocumentManager().query_all(
            conds=conds,
            orders=[DocumentTable.created_at.desc(), DocumentTable.id.desc()],
        )
        return [DocumentItem.model_validate(row) for row in rows]
