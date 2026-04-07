"""Agent 领域能力（供 Service 与 Tools 共用）。

目标：消除 tools 与 service 的重复实现，形成单一事实来源，避免行为漂移。
"""

from __future__ import annotations

import json
from typing import Any

from src.dao.orm.manager.document import DocumentManager
from src.dao.orm.table import DocumentTable
from src.dao.vector_store import VectorStoreManager
from src.data_schemas.api_schemas.rag import CitationItem


async def kb_search(
    *,
    scene_id: str,
    query: str,
    k: int = 6,
    citations_map: dict[tuple[int, str], CitationItem] | None = None,
) -> str:
    """知识库检索（统一实现）。

    Returns:
        JSON 字符串：{snippets: [...], citations: [...], message?: str}
    """
    vector_store = VectorStoreManager()
    docs = vector_store.search(scene_id, query, k=k) or []

    # fallback：向量库为空时，取最近入库的文档摘要/全文作为“弱检索”
    if not docs:
        rows = await DocumentManager().query_all(
            conds=[DocumentTable.scene_id == scene_id, DocumentTable.deleted_at.is_(None)],
            orders=[DocumentTable.created_at.desc()],
            limit=5,
        )
        for row in rows:
            text = (row.content or "") or (row.summary or "")
            if not text:
                continue
            docs.append(
                type(
                    "Doc",
                    (),
                    {"page_content": text[:1200], "metadata": {"document_id": row.id, "filename": row.filename}},
                )()
            )

    if not docs:
        return json.dumps({"snippets": [], "citations": [], "message": "知识库中未找到相关内容。"}, ensure_ascii=False)

    snippets: list[dict[str, Any]] = []
    citations: list[dict[str, Any]] = []

    for doc in docs:
        doc_id = int(doc.metadata.get("document_id", 0) or 0)
        filename = str(doc.metadata.get("filename", "未知文件"))
        quote = (doc.page_content or "")[:240]

        snippets.append({"document_id": doc_id, "filename": filename, "content": (doc.page_content or "")[:1000]})

        item = CitationItem(
            document_id=doc_id,
            source_label=filename,
            source_locator=f"doc-{doc_id}",
            quote=quote,
        )
        citations.append(item.model_dump())
        if isinstance(citations_map, dict):
            citations_map[(doc_id, filename)] = item

    return json.dumps({"snippets": snippets, "citations": citations}, ensure_ascii=False)

