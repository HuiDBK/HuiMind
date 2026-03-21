import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings.fake import FakeEmbeddings
from langchain_community.vectorstores import Chroma
from src import settings


class VectorStoreManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreManager, cls).__new__(cls)
            if settings.openai_api_key:
                try:
                    cls._instance.embeddings = OpenAIEmbeddings(
                        openai_api_key=settings.openai_api_key,
                        base_url=settings.openai_base_url,
                        model=settings.embedding_model_name,
                    )
                except TypeError:
                    cls._instance.embeddings = OpenAIEmbeddings(
                        openai_api_key=settings.openai_api_key, model=settings.embedding_model_name
                    )
            else:
                cls._instance.embeddings = FakeEmbeddings(size=1536)
            cls._instance.persist_directory = settings.chroma_persist_dir
            if not os.path.exists(cls._instance.persist_directory):
                os.makedirs(cls._instance.persist_directory)
        return cls._instance

    def get_collection(self, collection_name: str):
        return Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def add_documents(self, scene_id: str, documents: list):
        try:
            collection = self.get_collection(scene_id)
            collection.add_documents(documents)
            return True
        except Exception:
            return False

    def search(self, scene_id: str, query: str, k: int = 4, filter: dict = None):
        try:
            collection = self.get_collection(scene_id)
            return collection.similarity_search(query, k=k, filter=filter)
        except Exception:
            return []
