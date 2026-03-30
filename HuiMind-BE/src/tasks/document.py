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
from celery.signals import worker_process_init

@worker_process_init.connect
def init_worker_process(**kwargs):
    asyncio.run(init_orm())

async def _process_document(document_id: int):
    document_manager = DocumentManager()
    document = await document_manager.query_by_id(document_id)
    if not document:
        logger.error(f"Document {document_id} not found")
        return

    await document_manager.update(
        values={"status": "parsing"},
        conds=[DocumentTable.id == document_id]
    )

    try:
        if not document.oss_key:
            raise ValueError("missing oss_key")

        file_path = (Path(settings.file_storage_dir) / document.oss_key).resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 加载文档
        LOADER_MAP = {
            ".pdf": PyPDFLoader,
            ".txt": TextLoader,
            ".md": TextLoader,
            ".docx": Docx2txtLoader,
        }
        ext = file_path.suffix.lower()
        loader_cls = LOADER_MAP.get(ext)
        if not loader_cls:
            raise ValueError(f"不支持的文件类型: {ext}")

        raw_docs = loader_cls(str(file_path)).load()

        # 分块
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
        )
        chunks = text_splitter.split_documents(raw_docs)

        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "document_id": document_id,
                "chunk_id": f"{document_id}_{i}",
                "scene_id": document.scene_id,
                "filename": document.filename,
            })

        # 入库
        vector_store = VectorStoreManager()
        ok = vector_store.add_documents(document.scene_id, chunks)
        if not ok:
            raise Exception("向量入库失败")

        # 保存原文
        content_text = "\n\n".join([c.page_content for c in chunks])[:20000]
        await document_manager.update(
            values={"status": "ready", "content": content_text},
            conds=[DocumentTable.id == document_id]
        )
        logger.info(f"Document {document_id} processed, chunks={len(chunks)}")

    except Exception as e:
        logger.exception(f"Failed to process document {document_id}: {e}")
        await document_manager.update(
            values={"status": "failed", "summary": f"解析失败: {str(e)}"},
            conds=[DocumentTable.id == document_id]
        )

@celery_app.task(name="parse_document_task")
def parse_document_task(document_id: int):
    asyncio.run(_process_document(document_id))
