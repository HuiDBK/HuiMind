"""Agent 服务层实现。

该模块负责协调 Agent 的核心业务逻辑，包括：
- 问答处理（同步与流式）
- 知识库检索
- 练习题生成
- 薄弱点追踪
- 复习调度
- 评分评估
"""

import asyncio
import contextvars
import json
import time
from collections.abc import AsyncIterator
from datetime import timedelta

from langchain_core.messages import HumanMessage
from loguru import logger

from src.agents.agent_prompt import build_general_prompt, build_system_prompt
from src.agents.agent_tools import build_agent_tools
from src.agents.study_agent import AgentState, build_study_agent, run_agent_stream
from src.dao.orm.manager.buddy import BuddyProfileManager
from src.dao.orm.manager.document import DocumentManager
from src.dao.orm.manager.rag import QaRecordManager
from src.dao.orm.manager.review import ReviewTaskManager, WeakPointManager
from src.dao.orm.manager.scene import SceneManager
from src.dao.orm.table import BuddyProfileTable, DocumentTable, ReviewTaskTable, WeakPointTable
from src.dao.redis.session import append_qa_message, get_qa_history
from src.dao.vector_store import VectorStoreManager
from src.data_schemas.api_schemas.rag import AskData, AskRequest, CitationItem
from src.services.base import DomainSupportService, now_ts
from src.services.llm import LLMConfig, LLMProvider, LLMService

_RUN_CONTEXT: contextvars.ContextVar[dict | None] = contextvars.ContextVar("agent_run_context", default=None)


class AgentService(DomainSupportService):
    """Agent 服务类，负责处理用户问答、知识库检索、练习生成等核心业务。

    该服务协调 LLM、向量数据库、关系数据库等组件，提供完整的 AI 伴学能力。
    """

    def __init__(self):
        """初始化 AgentService。"""
        super().__init__()
        self.vector_store = VectorStoreManager()
        self.llm = LLMService.get(
            provider=LLMProvider.OPENAI,
            config=LLMConfig(temperature=0.3, streaming=True),
        )

    async def ask(self, payload: AskRequest) -> AskData:
        """处理用户问答请求（非流式）。

        Args:
            payload: 问答请求参数，包含 scene_id、session_id、question。

        Returns:
            AskData 包含 session_id、answer、citations 等信息。
        """
        user = await self.get_default_user()
        session_id = payload.session_id or int(time.time() * 1000)
        scene = await SceneManager().query_one(conds=[SceneManager.orm_table.scene_id == "general"])

        enabled_tools = (scene.enabled_tools if scene else []) or []
        persona = await self._resolve_persona(user_id=user.id)

        graph = build_study_agent(str(user.id), scene, persona)
        initial_state: AgentState = {
            "messages": [HumanMessage(content=payload.question)],
            "user_id": user.id,
            "scene": scene,
            "persona": persona,
            "tools_used": [],
            "iteration_count": 0,
        }

        try:
            result = await graph.ainvoke(initial_state)
            messages = result.get("messages", [])
            answer_text = ""
            if messages:
                last_msg = messages[-1]
                answer_text = getattr(last_msg, "content", "")

            if not answer_text:
                answer_text = "抱歉，我暂时无法回答这个问题。"

            citations = await self._extract_citations(scene.scene_id if scene else "general", payload.question)

            await self._persist_qa(
                user_id=user.id,
                scene_id=scene.scene_id if scene else "general",
                session_id=session_id,
                question=payload.question,
                answer=answer_text,
                citations=citations,
            )

            return AskData(
                session_id=session_id,
                answer=answer_text,
                citations=citations,
                insufficient_context=len(citations) == 0,
            )
        except Exception as e:
            logger.error(f"[AgentService] ask error: {e}")
            return AskData(
                session_id=session_id,
                answer=f"处理请求时发生错误：{str(e)}",
                citations=[],
                insufficient_context=True,
            )

    async def ask_stream(self, payload: AskRequest) -> AsyncIterator[dict]:
        """处理用户问答请求（流式）。

        Args:
            payload: 问答请求参数。

        Yields:
            事件字典，包含 type、content 等字段。
        """
        user = await self.get_default_user()
        session_id = payload.session_id or int(time.time() * 1000)
        scene = await SceneManager().query_one(conds=[SceneManager.orm_table.scene_id == "general"])

        enabled_tools = (scene.enabled_tools if scene else []) or []
        persona = await self._resolve_persona(user_id=user.id)

        graph = build_study_agent(str(user.id), scene, persona)

        answer_text = ""
        citations = []

        try:
            async for event in run_agent_stream(graph, user.id, scene, payload.question, persona):
                event_type = event.get("type")

                if event_type == "token":
                    answer_text += event.get("content", "")
                    yield {"code": 0, "message": "ok", "data": event}
                elif event_type == "tool_start":
                    yield {"code": 0, "message": "ok", "data": event}
                elif event_type == "tool_end":
                    yield {"code": 0, "message": "ok", "data": event}
                elif event_type == "status":
                    yield {"code": 0, "message": "ok", "data": event}
                elif event_type == "final":
                    answer_text = event.get("content", answer_text)
                    citations = await self._extract_citations(scene.scene_id if scene else "general", payload.question)
                    yield {
                        "code": 0,
                        "message": "ok",
                        "data": {
                            "type": "final",
                            "session_id": session_id,
                            "answer": answer_text,
                            "citations": [c.model_dump() for c in citations],
                            "insufficient_context": len(citations) == 0,
                        },
                    }
        except Exception as e:
            logger.error(f"[AgentService] ask_stream error: {e}")
            yield {"code": 1, "message": f"处理请求时发生错误：{str(e)}", "data": {"type": "error"}}
            return

        await self._persist_qa(
            user_id=user.id,
            scene_id=scene.scene_id if scene else "general",
            session_id=session_id,
            question=payload.question,
            answer=answer_text,
            citations=citations,
        )

    async def kb_search(self, *, scene_id: str, query: str) -> str:
        """在知识库中检索相关内容。

        Args:
            scene_id: 场景 ID。
            query: 检索查询词。

        Returns:
            JSON 格式的检索结果，包含 snippets 和 citations。
        """
        docs = self.vector_store.search(scene_id, query, k=6) or []
        if not docs:
            rows = await DocumentManager().query_all(
                conds=[DocumentTable.scene_id == scene_id, DocumentTable.deleted_at.is_(None)],
                orders=[DocumentTable.created_at.desc()],
                limit=5,
            )
            for row in rows:
                text = (row.content or "") or (row.summary or "")
                if text:
                    docs.append(
                        type(
                            "Doc",
                            (),
                            {"page_content": text[:1200], "metadata": {"document_id": row.id, "filename": row.filename}},
                        )()
                    )

        if not docs:
            return json.dumps({"snippets": [], "citations": [], "message": "知识库中未找到相关内容。"}, ensure_ascii=False)

        snippets = []
        citations = []
        ctx = _RUN_CONTEXT.get()
        citations_map = (ctx or {}).get("citations") if isinstance(ctx, dict) else None

        for doc in docs:
            doc_id = int(doc.metadata.get("document_id", 0) or 0)
            filename = str(doc.metadata.get("filename", "未知文件"))
            quote = (doc.page_content or "")[:240]
            snippets.append({"document_id": doc_id, "filename": filename, "content": doc.page_content[:1000]})
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

    async def generate_quiz(self, *, scene_id: str, raw_input: str) -> str:
        """生成练习题。

        Args:
            scene_id: 场景 ID。
            raw_input: 原始输入，格式为"知识点|题型"。

        Returns:
            生成的练习题内容。
        """
        parts = [p.strip() for p in (raw_input or "").split("|") if p.strip()]
        topic = parts[0] if parts else raw_input
        quiz_type = parts[1] if len(parts) > 1 else "综合"
        kb = await self.kb_search(scene_id=scene_id, query=topic)
        kb_obj = self._safe_json_loads(kb)
        context = "\n\n".join([s.get("content", "") for s in kb_obj.get("snippets", [])])[:6000]
        prompt = (
            "你是学习助手，请基于给定资料内容生成练习题。\n"
            f"题型偏好：{quiz_type}\n"
            "要求：输出 JSON，包含 questions 数组，每题含 question, options(如适用), answer, explanation。\n"
            "资料内容：\n"
            f"{context}\n"
            f"知识点：{topic}\n"
        )
        resp = await asyncio.to_thread(self.llm.invoke, prompt)
        return getattr(resp, "content", str(resp))

    async def schedule_review(self, *, scene_id: str, concept: str) -> str:
        """安排复习计划。

        Args:
            scene_id: 场景 ID。
            concept: 知识点名称。

        Returns:
            安排结果描述。
        """
        concept = (concept or "").strip()
        if not concept:
            return "请输入要加入复习计划的知识点。"
        await self.upsert_weak_point(scene_id=scene_id, concept=concept, source_type="agent", mastery_level="reviewing")
        due_at = now_ts() + timedelta(days=1)
        exists = await ReviewTaskManager().query_one(
            conds=[
                ReviewTaskTable.scene_id == scene_id,
                ReviewTaskTable.concept == concept,
                ReviewTaskTable.status == "pending",
                ReviewTaskTable.deleted_at.is_(None),
            ]
        )
        if not exists:
            await ReviewTaskManager().add({"scene_id": scene_id, "concept": concept, "due_at": due_at, "status": "pending"})
        return (
            f"已将「{concept}」加入复习计划。\n"
            f"推荐下次复习时间：{due_at.strftime('%Y-%m-%d')}\n"
            "推荐间隔：1天 → 2天 → 4天 → 7天 → 15天 → 30天"
        )

    async def update_weakness(self, *, scene_id: str, raw_input: str) -> str:
        """更新薄弱点记录。

        Args:
            scene_id: 场景 ID。
            raw_input: 原始输入文本。

        Returns:
            更新结果描述。
        """
        text = (raw_input or "").strip()
        if not text:
            return "请输入要记录的薄弱点或包含知识点的文本。"
        concepts = self.extract_keywords(text)
        if not concepts:
            concepts = [text[:50]]
        for concept in concepts[:5]:
            await self.upsert_weak_point(scene_id=scene_id, concept=concept, source_type="agent", mastery_level="weak")
        return "已更新薄弱点：" + "、".join(concepts[:5])

    async def evaluate_rubric(self, *, scene_id: str, eval_rubric: dict, raw_input: str) -> str:
        """按评分规则评估用户输入。

        Args:
            scene_id: 场景 ID。
            eval_rubric: 评分规则配置。
            raw_input: 用户输入文本。

        Returns:
            评估结果描述。
        """
        rubric = json.dumps(eval_rubric or {}, ensure_ascii=False)
        prompt = (
            "你是学习助手，请按评分规则对用户文本进行评分并给出改进建议。\n"
            "输出要求：分项评分 + 总结 + 3 条可执行改进建议。\n"
            f"评分规则：{rubric}\n"
            f"用户文本：{raw_input}\n"
        )
        resp = await asyncio.to_thread(self.llm.invoke, prompt)
        return getattr(resp, "content", str(resp))

    @staticmethod
    def web_search(*, raw_input: str) -> str:
        """联网搜索（MVP 阶段占位实现）。

        Args:
            raw_input: 搜索关键词。

        Returns:
            提示信息。
        """
        return (
            f"[外部资料补充请求：{raw_input}]\n"
            "MVP 阶段暂未接入实时搜索。你可以上传时政/参考资料，我会从资料里检索并总结。"
        )

    async def query_memory(self, *, scene_id: str, query: str) -> str:
        """查询用户学习记忆。

        Args:
            scene_id: 场景 ID。
            query: 查询内容。

        Returns:
            学习记录摘要。
        """
        wps = await WeakPointManager().query_all(
            conds=[WeakPointTable.scene_id == scene_id, WeakPointTable.deleted_at.is_(None)],
            orders=[WeakPointTable.next_review_at.asc()],
            limit=10,
        )
        tasks = await ReviewTaskManager().query_all(
            conds=[
                ReviewTaskTable.scene_id == scene_id,
                ReviewTaskTable.status == "pending",
                ReviewTaskTable.deleted_at.is_(None),
            ],
            orders=[ReviewTaskTable.due_at.asc()],
            limit=10,
        )
        lines = []
        if wps:
            lines.append("薄弱点：")
            for wp in wps[:6]:
                lines.append(f"- {wp.concept}（下次复习：{wp.next_review_at.strftime('%Y-%m-%d')}）")
        if tasks:
            lines.append("待复习：")
            for t in tasks[:6]:
                lines.append(f"- {t.concept}（到期：{t.due_at.strftime('%Y-%m-%d')}）")
        if not lines:
            return "暂无历史记忆记录。"
        return "\n".join(lines)

    async def _resolve_persona(self, *, user_id: int) -> str:
        """获取用户的 AI 人设风格。

        Args:
            user_id: 用户 ID。

        Returns:
            人设风格名称，默认"严师型"。
        """
        persona = "严师型"
        try:
            buddy = await BuddyProfileManager().query_one(
                conds=[BuddyProfileTable.user_id == user_id, BuddyProfileTable.deleted_at.is_(None)],
                orders=[BuddyProfileTable.id.asc()],
            )
            if buddy and buddy.persona:
                persona = buddy.persona
        except Exception:
            pass
        return persona

    async def _extract_citations(self, scene_id: str, query: str) -> list[CitationItem]:
        """从检索结果中提取引用信息。

        Args:
            scene_id: 场景 ID。
            query: 查询内容。

        Returns:
            引用项列表。
        """
        kb_result = await self.kb_search(scene_id=scene_id, query=query)
        kb_obj = self._safe_json_loads(kb_result)
        citations = []
        for c in kb_obj.get("citations", []):
            citations.append(CitationItem(**c))
        return citations

    async def _persist_qa(
        self,
        *,
        user_id: int,
        scene_id: str,
        session_id: str,
        question: str,
        answer: str,
        citations: list[CitationItem],
    ) -> None:
        """持久化问答记录。

        Args:
            user_id: 用户 ID。
            scene_id: 场景 ID。
            session_id: 会话 ID。
            question: 用户问题。
            answer: AI 回答。
            citations: 引用列表。
        """
        try:
            await append_qa_message(user_id=user_id, scene_id=scene_id, session_id=session_id, role="user", content=question)
            await append_qa_message(user_id=user_id, scene_id=scene_id, session_id=session_id, role="assistant", content=answer)
        except Exception:
            pass

        await QaRecordManager().add(
            {
                "scene_id": scene_id,
                "session_id": session_id,
                "question": question,
                "answer": answer,
                "citations": [item.model_dump() for item in citations],
                "insufficient_context": 0 if citations else 1,
            }
        )

    @staticmethod
    def _safe_json_loads(raw: str) -> dict:
        """安全解析 JSON 字符串。

        Args:
            raw: JSON 字符串。

        Returns:
            解析后的字典，解析失败返回空字典。
        """
        try:
            return json.loads(raw)
        except Exception:
            return {}
