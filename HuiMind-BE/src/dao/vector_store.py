"""向量存储管理模块。

该模块负责管理 ChromaDB 向量数据库的连接和操作，包括：
- Embedding 模型初始化（使用阿里云百炼）
- 向量数据库集合管理
- 文档向量化与存储
- 相似性搜索
"""

import os

import dashscope
from langchain_dashscope import DashScopeEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings.fake import FakeEmbeddings
from langchain_chroma import Chroma
from src import settings


class VectorStoreManager:
    """向量存储管理器。

    单例模式实现，负责管理 Embedding 模型和 ChromaDB 连接。
    使用阿里云百炼的 Embedding API 进行文本向量化。
    """
    
    _instance = None
    
    def __new__(cls):
        """创建或返回 VectorStoreManager 单例实例。

        Returns:
            VectorStoreManager 实例。
        """
        if cls._instance is None:
            cls._instance = super(VectorStoreManager, cls).__new__(cls)
            if settings.dashscope_api_key:
                dashscope.api_key = settings.dashscope_api_key
                cls._instance.embeddings = DashScopeEmbeddings(
                    model=settings.embedding_model_name,
                )
            else:
                cls._instance.embeddings = FakeEmbeddings(size=1536)
            cls._instance.persist_directory = settings.chroma_persist_dir
            if not os.path.exists(cls._instance.persist_directory):
                os.makedirs(cls._instance.persist_directory)
        return cls._instance

    def get_collection(self, collection_name: str):
        """获取或创建向量数据库集合。

        Args:
            collection_name: 集合名称。

        Returns:
            Chroma 向量数据库集合实例。
        """
        return Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )

    def add_documents(self, scene_id: str, documents: list):
        """将文档添加到向量数据库。

        Args:
            scene_id: 场景 ID，用作集合名称。
            documents: 要添加的文档列表。

        Returns:
            是否成功添加文档。
        """
        try:
            collection = self.get_collection(scene_id)
            collection.add_documents(documents)
            return True
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to add documents to vector store: {e}")
            return False

    def search(self, scene_id: str, query: str, k: int = 4, filter: dict = None):
        """在向量数据库中搜索相似文档。

        Args:
            scene_id: 场景 ID，用作集合名称。
            query: 查询文本。
            k: 返回的文档数量，默认为 4。
            filter: 过滤条件字典。

        Returns:
            相似文档列表。
        """
        try:
            collection = self.get_collection(scene_id)
            return collection.similarity_search(query, k=k, filter=filter)
        except Exception as e:
            from loguru import logger
            logger.error(f"Failed to search documents: {e}")
            return []
