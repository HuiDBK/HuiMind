from typing import List, Dict, Optional
import jieba

from langchain_core.documents import Document
from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers.document_compressors import LLMChainExtractor

from src.services.base import BaseService
from src.services.llm import LLMService, LLMProvider, LLMConfig
from src.dao.vector_store import VectorStoreManager


class RAGService(BaseService):
    """RAG 检索服务（支持查询增强 + 混合检索 + rerank + 压缩）。"""
    # BM25 缓存（按知识库维度）
    BM25_CACHE: Dict[str, BM25Retriever] = {}

    def __init__(self):
        """初始化 RAG 组件。"""
        super().__init__()

        self.llm = LLMService.get(
            provider=LLMProvider.OPENAI,
            config=LLMConfig(temperature=0.1),
        )

        self.vector_store_manager = VectorStoreManager()


    def _tokenizer(self, text: str) -> List[str]:
        """中文分词。

        Args:
            text: 输入文本

        Returns:
            List[str]: 分词结果
        """
        return list(jieba.cut(text))

    async def rewrite_query(self, query: str) -> str:
        """查询改写（提升检索匹配度）。"""
        prompt = f"""
你是一个搜索优化助手，请将用户问题改写为适合检索的关键词查询。

要求：
1. 不超过50个字
2. 保留核心语义
3. 去除冗余描述
4. 只输出结果，不解释

问题：
{query}
"""
        resp = await self.llm.ainvoke(prompt)
        return resp.content.strip()

    async def step_back_query(self, query: str) -> str:
        """问题抽象（提升泛化召回能力）。"""
        prompt = f"""
请将用户问题抽象为更通用的问题。

要求：
1. 提炼本质
2. 去掉具体细节
3. 输出一句话
4. 不解释

问题：
{query}
"""
        resp = await self.llm.ainvoke(prompt)
        return resp.content.strip()

    async def hyde_query(self, query: str) -> str:
        """生成假想答案（用于 embedding 检索增强）。"""
        prompt = f"""
请生成一个高质量专业回答。

要求：
1. 信息密集
2. 直接回答问题
3. 不解释
4. 不超过100字

问题：
{query}
"""
        resp = await self.llm.ainvoke(prompt)
        return resp.content.strip()

    async def multi_query(self, query: str, n: int = 3) -> List[str]:
        """生成多个等价查询（提升召回覆盖率）。

        Args:
            query: 原始问题
            n: 查询数量

        Returns:
            List[str]
        """
        prompt = f"""
请基于用户问题生成多个不同表达方式的查询。

要求：
1. 语义一致
2. 表达不同
3. 每行一个
4. 不解释
5. 共{n}个

问题：
{query}
"""
        resp = await self.llm.ainvoke(prompt)

        queries = [
            line.strip()
            for line in resp.content.split("\n")
            if line.strip()
        ]

        return queries[:n]

    def _build_retriever(self, scene_id: str, top_k: int = 6):
        """构建混合检索（向量 + BM25）。"""
        vs = self.vector_store_manager.get_collection(scene_id)

        vector_retriever = vs.as_retriever(search_kwargs={"k": top_k})

        # 构建 / 复用 BM25
        if scene_id not in self._bm25_cache:
            existing = vs.get(limit=1000)

            if not existing["documents"]:
                return vector_retriever

            docs = [
                Document(page_content=text, metadata=meta)
                for text, meta in zip(
                    existing["documents"],
                    existing["metadatas"],
                )
            ]

            bm25 = BM25Retriever.from_documents(
                docs,
                tokenizer=self._tokenizer,
            )

            self._bm25_cache[scene_id] = bm25

        bm25_retriever = self._bm25_cache[scene_id]
        bm25_retriever.k = top_k

        return EnsembleRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            weights=[0.7, 0.3],
        )

    def _wrap_with_compression(self, retriever):
        """使用 LLM 对召回文档进行压缩。"""
        compressor = LLMChainExtractor.from_llm(self.llm)

        return ContextualCompressionRetriever(
            base_retriever=retriever,
            base_compressor=compressor,
        )

    async def rerank(
        self,
        query: str,
        docs: List[Document],
        top_k: int,
    ) -> List[Document]:
        """基于 LLM 的重排序（后续可改成专门的rerank模型）"""
        texts = [doc.page_content[:300] for doc in docs]

        prompt = f"""
请根据问题对文档按相关性排序。

要求：
1. 返回最相关的{top_k}个编号
2. 使用英文逗号分隔，如：0,2,1
3. 不要解释

问题：
{query}

文档：
{chr(10).join([f"{i}. {t}" for i, t in enumerate(texts)])}
"""

        resp = await self.llm.ainvoke(prompt)

        try:
            indices = [
                int(x)
                for x in resp.content.replace(" ", "").split(",")
            ]
        except Exception:
            return docs[:top_k]

        return [docs[i] for i in indices if 0 <= i < len(docs)][:top_k]

    def clear_bm25_cache(self, scene_id: Optional[str] = None) -> None:
        """清理 BM25 缓存。

        Args:
            scene_id: 指定知识库（为空则清全部）
        """
        if scene_id:
            self.BM25_CACHE.pop(scene_id, None)
        else:
            self.BM25_CACHE.clear()

    async def retrieve(
        self,
        scene_id: str,
        query: str,
        k: int = 4,
        use_rewrite: bool = True,
        use_step_back: bool = False,
        use_hyde: bool = False,
        use_multi_query: bool = False,
        use_rerank: bool = False,
        use_compression: bool = False,
    ) -> List[Document]:
        """统一检索入口（支持多策略组合）。

        Args:
            scene_id: 知识库场景 ID。
            query: 用户问题或检索词。
            k: 最终返回的文档数量。
            use_rewrite: 是否将 query 改写为更适合检索的关键词形式。
                        适合 query 口语化、冗余描述较多的场景。
                        有 Agent 改写时建议关闭，避免重复调用 LLM。
            use_step_back: 是否将 query 抽象为更泛化的问题以提升召回覆盖率。
                        适合 query 过于具体、向量匹配命中率低的场景。
            use_hyde: 是否先生成假想答案再用其 embedding 检索。
                    适合问答型 query，对知识密集型文档效果较好。
            use_multi_query: 是否生成多个等价查询并合并结果以提升召回多样性。
                            会额外产生 n 次 LLM 调用，注意成本。
            use_rerank: 是否使用 LLM 对召回文档重排序。
                        召回文档较多、精排要求高时开启，会额外产生一次 LLM 调用。
            use_compression: 是否对召回文档做上下文压缩，只保留与 query 相关的片段。
                            适合文档较长、噪声较多的场景，开启后会增加延迟。

        Returns:
            List[Document]: 按相关性排序的文档列表，长度不超过 k。
        """   

        # 1. 并发执行查询增强
        enhancement_tasks = {
            "rewrite": self.rewrite_query(query) if use_rewrite else None,
            "step_back": self.step_back_query(query) if use_step_back else None,
            "hyde": self.hyde_query(query) if use_hyde else None,
            "multi": self.multi_query(query) if use_multi_query else None,
        }

        active = {k: v for k, v in enhancement_tasks.items() if v is not None}
        results = await asyncio.gather(*active.values(), return_exceptions=True)

        queries = [query]
        for key, result in zip(active.keys(), results):
            if isinstance(result, Exception):
                logger.warning(f"[RAG] query enhancement '{key}' failed: {result}")
                continue
            if isinstance(result, list):
                queries.extend(result)
            else:
                queries.append(result)

        queries = list(set(queries))

        # 2. 构建检索器
        retriever = self._build_retriever(scene_id, top_k=k + 6)
        if use_compression:
            retriever = self._wrap_with_compression(retriever)

        # 3. 并发检索所有 query
        retrieve_results = await asyncio.gather(
            *[retriever.ainvoke(q) for q in queries],
            return_exceptions=True,
        )

        all_docs = []
        for r in retrieve_results:
            if isinstance(r, Exception):
                logger.warning(f"[RAG] retrieval failed: {r}")
                continue
            all_docs.extend(r)

        # 4. 去重
        unique_docs = list({doc.page_content: doc for doc in all_docs}.values())

        # 5. rerank 或截断
        if use_rerank:
            return await self.rerank(query, unique_docs, k)

        return unique_docs[:k]