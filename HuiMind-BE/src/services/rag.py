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
from src.services.base import DomainSupportService, now_ts


class RagService(DomainSupportService):
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model_name=settings.model_name,
            temperature=0,
        )
        self.vector_store_manager = VectorStoreManager()

    async def ask_question(self, payload: AskRequest) -> AskData:
        scene_id = payload.scene_id
        query = payload.question
        
        # 1. 向量检索
        collection = self.vector_store_manager.get_collection(scene_id)
        docs = self.vector_store_manager.search(scene_id, query, k=4)
        
        if not docs:
            # 这里的 fallback 逻辑可以保留一部分原有的 Mock 逻辑，或者直接返回资料不足
            return AskData(
                answer="抱歉，在当前的知识库中没有找到相关信息。你可以尝试换个问题，或者补充更多资料。",
                citations=[],
                session_id=payload.session_id or str(int(now_ts().timestamp())),
                insufficient_context=True
            )

        # 2. 组装提示词
        prompt_template = """你是一个 HuiMind AI 伴学助手。请根据以下提供的参考资料回答用户的问题。
如果你在资料中找不到答案，请诚实地告诉用户你不知道，不要胡编乱造。

参考资料:
{context}

用户问题: {question}

回答要求:
1. 语言简洁专业。
2. 如果可能，请在回答中指出参考了哪些资料。
3. 如果资料不足以回答，请提示用户。

你的回答:"""
        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        # 3. 执行检索问答
        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=collection.as_retriever(search_kwargs={"k": 4}),
            chain_type_kwargs={"prompt": PROMPT},
            return_source_documents=True,
        )
        
        result = await asyncio.to_thread(chain.invoke, {"query": query})
        answer = result["result"]
        source_docs = result["source_documents"]

        # 4. 提取引用
        citations = []
        for doc in source_docs:
            citations.append(CitationItem(
                document_id=doc.metadata.get("document_id", 0),
                source_label=doc.metadata.get("filename", "未知文件"),
                source_locator=f"doc-{doc.metadata.get('document_id', 'unknown')}",
                quote=doc.page_content[:120] + "...",
            ))

        # 5. 记录问答到数据库
        session_id = payload.session_id or str(int(now_ts().timestamp()))
        await QaRecordManager().add(
            {
                "scene_id": scene_id,
                "session_id": session_id,
                "question": query,
                "answer": answer,
                "citations": [item.model_dump() for item in citations],
                "insufficient_context": 0,
            }
        )

        return AskData(
            answer=answer,
            citations=citations,
            session_id=session_id,
            insufficient_context=False
        )
