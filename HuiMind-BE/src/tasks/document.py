import asyncio
import os
from pathlib import Path
from loguru import logger
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src import settings
from src.tasks.celery_app import celery_app
from src.dao.orm.manager.document import DocumentManager
from src.dao.orm.table import DocumentTable
from src.dao.vector_store import VectorStoreManager
from src.dao import init_orm


async def _process_document(document_id: int):
    await init_orm()
    document_manager = DocumentManager()
    document = await document_manager.query_by_id(document_id)
    if not document:
        logger.error(f"Document {document_id} not found")
        return

    await document_manager.update(values={"status": "parsing"}, conds=[DocumentTable.id == document_id])

    try:
        if not document.oss_key:
            raise ValueError("missing oss_key")

        file_path = (Path(settings.file_storage_dir) / document.oss_key).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found")

        ext = file_path.suffix.lower()
        if ext == ".pdf":
            loader = PyPDFLoader(str(file_path))
        else:
            loader = TextLoader(str(file_path))

        raw_docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(raw_docs)
        for chunk in chunks:
            chunk.metadata.update(
                {
                "document_id": document_id,
                "scene_id": document.scene_id,
                "filename": document.filename,
                }
            )

        vector_store = VectorStoreManager()
        ok = vector_store.add_documents(document.scene_id, chunks)
        if not ok:
            content_text = "\n\n".join([doc.page_content for doc in chunks])[:20000]
            await document_manager.update(values={"content": content_text}, conds=[DocumentTable.id == document_id])

        await document_manager.update(values={"status": "ready"}, conds=[DocumentTable.id == document_id])
        logger.info(f"Document {document_id} processed successfully")

    except Exception as e:
        logger.exception(f"Failed to process document {document_id}: {e}")
        await document_manager.update(values={"status": "failed", "summary": f"解析失败: {str(e)}"}, conds=[DocumentTable.id == document_id])


@celery_app.task(name="parse_document_task")
def parse_document_task(document_id: int):
    asyncio.run(_process_document(document_id))
