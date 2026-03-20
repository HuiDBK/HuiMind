"""RAG services."""

from src.dao.orm.manager.document import DocumentManager
from src.dao.orm.manager.rag import QaRecordManager
from src.dao.orm.table import DocumentTable
from src.data_schemas.api_schemas.rag import AskData, AskRequest, CitationItem
from src.services.base import DomainSupportService, now_ts


class RagService(DomainSupportService):
    async def ask_question(self, payload: AskRequest) -> AskData:
        documents = await DocumentManager().query_all(
            conds=[DocumentTable.scene_id == payload.scene_id, DocumentTable.deleted_at.is_(None)],
            orders=[DocumentTable.created_at.desc()],
            limit=2,
        )
        citations = [
            CitationItem(
                document_id=document.id,
                source_label=document.filename,
                source_locator=f"document-{document.id}",
                quote=(document.summary or "暂无摘要")[:120],
            )
            for document in documents
        ]
        answer = (
            f"基于 {payload.scene_id} 场景已有资料，我建议先围绕“{payload.question[:18]}”对应的核心概念、实践案例和易错点来复盘。"
            "如果你愿意，我可以继续把它拆成 3 个更适合复习的知识点。"
        )
        session_id = payload.session_id or int(now_ts().timestamp())
        await QaRecordManager().add(
            {
                "scene_id": payload.scene_id,
                "session_id": session_id,
                "question": payload.question,
                "answer": answer,
                "citations": [item.model_dump() for item in citations],
                "insufficient_context": 0,
            }
        )
        return AskData(session_id=session_id, answer=answer, citations=citations, insufficient_context=False)
