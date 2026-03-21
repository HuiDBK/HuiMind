"""Agent services."""

import asyncio
import contextvars
import json
from collections.abc import AsyncIterator
from datetime import timedelta

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from src import settings
from src.agents.agent_prompt import build_system_prompt
from src.agents.agent_tools import build_agent_tools
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


_RUN_CONTEXT: contextvars.ContextVar[dict | None] = contextvars.ContextVar("agent_run_context", default=None)


class AgentService(DomainSupportService):
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model_name=settings.model_name,
            temperature=0.3,
            streaming=True,
        )
        self.vector_store = VectorStoreManager()

    async def ask(self, payload: AskRequest) -> AskData:
        user = await self.get_default_user()
        session_id = payload.session_id or int(now_ts().timestamp())
        scene = await SceneManager().query_one(conds=[SceneManager.orm_table.scene_id == payload.scene_id])
        enabled_tools = (scene.enabled_tools if scene else []) or []
        persona = await self._resolve_persona(user_id=user.id)

        system_prompt = build_system_prompt(scene=scene, persona=persona)
        tools = build_agent_tools(
            service=self,
            scene_id=payload.scene_id,
            enabled_tools=enabled_tools,
            eval_rubric=(scene.eval_rubric if scene else {}) or {},
        )
        agent = create_agent(self.llm, tools, system_prompt=system_prompt)

        history = await self._load_history(user_id=user.id, scene_id=payload.scene_id, session_id=session_id)
        messages = self._build_messages(history=history, question=payload.question)

        token = _RUN_CONTEXT.set({"citations": {}})
        try:
            out = await agent.ainvoke({"messages": messages})
        except Exception:
            _RUN_CONTEXT.reset(token)
            answer_text = "Agent 调用模型失败：请检查 OPENAI_API_KEY、OPENAI_API_BASE 与模型名称是否正确。"
            citations: list[CitationItem] = []
            return AskData(session_id=session_id, answer=answer_text, citations=citations, insufficient_context=True)

        ctx = _RUN_CONTEXT.get() or {}
        _RUN_CONTEXT.reset(token)

        answer_text = self._extract_final_answer(out) or "我没有得到稳定的回答结果。"
        citations = list((ctx.get("citations") or {}).values())

        await self._persist_qa(
            user_id=user.id,
            scene_id=payload.scene_id,
            session_id=session_id,
            question=payload.question,
            answer=answer_text,
            citations=citations,
        )

        return AskData(
            session_id=session_id,
            answer=answer_text,
            citations=citations,
            insufficient_context=False if citations else True,
        )

    async def ask_stream(self, payload: AskRequest) -> AsyncIterator[dict]:
        user = await self.get_default_user()
        session_id = payload.session_id or int(now_ts().timestamp())
        scene = await SceneManager().query_one(conds=[SceneManager.orm_table.scene_id == payload.scene_id])
        enabled_tools = (scene.enabled_tools if scene else []) or []
        persona = await self._resolve_persona(user_id=user.id)

        system_prompt = build_system_prompt(scene=scene, persona=persona)
        tools = build_agent_tools(
            service=self,
            scene_id=payload.scene_id,
            enabled_tools=enabled_tools,
            eval_rubric=(scene.eval_rubric if scene else {}) or {},
        )
        agent = create_agent(self.llm, tools, system_prompt=system_prompt)

        history = await self._load_history(user_id=user.id, scene_id=payload.scene_id, session_id=session_id)
        messages = self._build_messages(history=history, question=payload.question)

        token = _RUN_CONTEXT.set({"citations": {}})
        answer_text = ""
        tool_step = 0

        yield {
            "code": 0,
            "message": "ok",
            "data": {"type": "status", "session_id": session_id, "content": "开始处理请求，准备调用工具与生成回答。"},
        }

        try:
            async for ev in agent.astream_events({"messages": messages}, version="v2"):
                evt = ev.get("event")
                name = ev.get("name")
                data = ev.get("data") or {}

                if evt == "on_tool_start":
                    tool_step += 1
                    yield {
                        "code": 0,
                        "message": "ok",
                        "data": {
                            "type": "tool_start",
                            "step": tool_step,
                            "tool_name": name,
                            "input": data.get("input"),
                        },
                    }
                    continue

                if evt == "on_tool_end":
                    tool_step += 1
                    output = data.get("output")
                    if not isinstance(output, str):
                        output = getattr(output, "content", None) or str(output)
                    if isinstance(output, str) and len(output) > 2000:
                        output = output[:2000]
                    yield {
                        "code": 0,
                        "message": "ok",
                        "data": {
                            "type": "tool_end",
                            "step": tool_step,
                            "tool_name": name,
                            "output": output,
                        },
                    }
                    continue

                if evt == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    piece = getattr(chunk, "content", None)
                    if piece:
                        answer_text += piece
                        yield {"code": 0, "message": "ok", "data": {"type": "token", "content": piece}}
                    continue

                if evt == "on_chain_end" and name == "LangGraph":
                    final = self._extract_final_answer(data.get("output"))
                    if final:
                        answer_text = final
        except Exception:
            _RUN_CONTEXT.reset(token)
            yield {"code": 1, "message": "Agent 调用模型失败", "data": {"type": "error", "session_id": session_id}}
            return

        ctx = _RUN_CONTEXT.get() or {}
        _RUN_CONTEXT.reset(token)
        citations = list((ctx.get("citations") or {}).values())

        await self._persist_qa(
            user_id=user.id,
            scene_id=payload.scene_id,
            session_id=session_id,
            question=payload.question,
            answer=answer_text,
            citations=citations,
        )

        yield {
            "code": 0,
            "message": "ok",
            "data": {
                "type": "final",
                "session_id": session_id,
                "answer": answer_text,
                "citations": [c.model_dump() for c in citations],
                "insufficient_context": False if citations else True,
            },
        }

    async def _resolve_persona(self, *, user_id: int) -> str:
        persona = "陪伴型"
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

    async def _load_history(self, *, user_id: int, scene_id: str, session_id: int) -> list[dict]:
        try:
            return await get_qa_history(user_id=user_id, scene_id=scene_id, session_id=session_id)
        except Exception:
            return []

    @staticmethod
    def _build_messages(*, history: list[dict], question: str) -> list[dict]:
        msgs = []
        for item in history[-10:]:
            role = item.get("role") or ""
            if role not in {"user", "assistant"}:
                continue
            content = item.get("content") or ""
            if content:
                msgs.append({"role": role, "content": content})
        msgs.append({"role": "user", "content": question})
        return msgs

    @staticmethod
    def _extract_final_answer(output) -> str | None:
        if not isinstance(output, dict):
            return None
        msgs = output.get("messages") or []
        for msg in reversed(msgs):
            content = getattr(msg, "content", None)
            if isinstance(content, str) and content.strip():
                return content.strip()
        return None

    async def _persist_qa(
        self,
        *,
        user_id: int,
        scene_id: str,
        session_id: int,
        question: str,
        answer: str,
        citations: list[CitationItem],
    ) -> None:
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

    async def kb_search(self, *, scene_id: str, query: str) -> str:
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
                    docs.append(type("Doc", (), {"page_content": text[:1200], "metadata": {"document_id": row.id, "filename": row.filename}})())

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
        return (
            f"[外部资料补充请求：{raw_input}]\n"
            "MVP 阶段暂未接入实时搜索。你可以上传时政/参考资料，我会从资料里检索并总结。"
        )

    async def query_memory(self, *, scene_id: str, query: str) -> str:
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

    @staticmethod
    def _safe_json_loads(raw: str) -> dict:
        try:
            return json.loads(raw)
        except Exception:
            return {}
