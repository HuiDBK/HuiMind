"""RAG services."""

import asyncio
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

from src import settings
from src.dao.orm.manager.document import DocumentManager
from src.dao.orm.manager.rag import QaRecordManager
from src.dao.orm.table import DocumentTable
from src.dao.vector_store import VectorStoreManager
from src.data_schemas.api_schemas.rag import AskData, AskRequest, CitationItem
from src.services.base import BaseService


class RagService(BaseService):
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model_name=settings.model_name,
            temperature=0,
        )
        self.vector_store_manager = VectorStoreManager()