"""Career services."""

from fastapi import HTTPException, status

from src.dao.orm.manager.career import InterviewSessionManager, InterviewTurnManager, ResumeDiagnosisManager
from src.dao.orm.table import InterviewSessionTable, InterviewTurnTable
from src.data_schemas.api_schemas.career import (
    InterviewAnswerData,
    InterviewAnswerRequest,
    InterviewQuestionItem,
    InterviewSessionCreateData,
    InterviewSessionCreateRequest,
    InterviewSessionDetailData,
    InterviewTurnDetail,
    ResumeDiagnosisData,
    ResumeDiagnosisRequest,
    RewriteSuggestionItem,
    RiskyPhraseItem,
)
from src.services.base import DomainSupportService


class CareerService(DomainSupportService):
    async def resume_diagnosis(self, payload: ResumeDiagnosisRequest) -> ResumeDiagnosisData:
        resume_doc = await self.get_document_or_404(payload.resume_doc_id)
        jd_doc = await self.get_document_or_404(payload.jd_doc_id)
        matched_keywords = self.extract_keywords(resume_doc.summary + " " + (resume_doc.content or ""))
        jd_keywords = self.extract_keywords(jd_doc.filename + " " + (jd_doc.content or "") + " " + jd_doc.summary)
        missing_keywords = [keyword for keyword in jd_keywords if keyword not in matched_keywords][:3]
        matched_keywords = [keyword for keyword in matched_keywords if keyword in jd_keywords][:4] or matched_keywords[:4]
        match_score = round(max(55.0, min(96.0, 60.0 + len(matched_keywords) * 8 - len(missing_keywords) * 3)), 1)
        risky_phrases = [{"original": "负责一些后端开发工作", "reason": "表达泛化，没有体现具体动作和结果。"}]
        rewrite_suggestions = [{
            "original": "负责一些后端开发工作",
            "rewritten": "负责 FastAPI 后端接口开发与 MySQL 数据建模，支撑核心业务模块上线。",
        }]
        summary = "你的技术栈和岗位目标已经有一定匹配度，下一步重点补齐成果量化和高并发表达。"
        diagnosis_id = await ResumeDiagnosisManager().add(
            {
                "scene_id": payload.scene_id,
                "resume_doc_id": payload.resume_doc_id,
                "jd_doc_id": payload.jd_doc_id,
                "match_score": match_score,
                "matched_keywords": matched_keywords,
                "missing_keywords": missing_keywords,
                "risky_phrases": risky_phrases,
                "rewrite_suggestions": rewrite_suggestions,
                "summary": summary,
            }
        )
        row = await ResumeDiagnosisManager().query_by_id(diagnosis_id)
        return ResumeDiagnosisData(
            diagnosis_id=row.id,
            match_score=row.match_score,
            matched_keywords=row.matched_keywords or [],
            missing_keywords=row.missing_keywords or [],
            risky_phrases=[RiskyPhraseItem(**item) for item in (row.risky_phrases or [])],
            rewrite_suggestions=[RewriteSuggestionItem(**item) for item in (row.rewrite_suggestions or [])],
            summary=row.summary,
        )

    async def create_interview_session(self, payload: InterviewSessionCreateRequest) -> InterviewSessionCreateData:
        await self.get_document_or_404(payload.jd_doc_id)
        session_id = await InterviewSessionManager().add(
            {
                "scene_id": payload.scene_id,
                "jd_doc_id": payload.jd_doc_id,
                "mode": payload.mode,
                "status": "in_progress",
                "overall_score": 0,
                "summary": "模拟面试已创建，等待你的第一轮回答。",
            }
        )
        for index, question in enumerate(self.build_interview_questions(payload.mode), start=1):
            await InterviewTurnManager().add({"session_id": session_id, "question_order": index, "question": question})
        turns = await InterviewTurnManager().query_all(
            conds=[InterviewTurnTable.session_id == session_id, InterviewTurnTable.deleted_at.is_(None)],
            orders=[InterviewTurnTable.question_order.asc()],
        )
        return InterviewSessionCreateData(
            session_id=session_id,
            status="in_progress",
            questions=[InterviewQuestionItem(turn_id=turn.id, question_order=turn.question_order, question=turn.question) for turn in turns],
        )

    async def get_interview_session(self, session_id: int) -> InterviewSessionDetailData:
        session = await InterviewSessionManager().query_by_id(session_id)
        if not session or session.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模拟面试不存在")
        turns = await InterviewTurnManager().query_all(
            conds=[InterviewTurnTable.session_id == session_id, InterviewTurnTable.deleted_at.is_(None)],
            orders=[InterviewTurnTable.question_order.asc()],
        )
        return InterviewSessionDetailData(
            id=session.id,
            scene_id=session.scene_id,
            status=session.status,
            overall_score=session.overall_score,
            summary=session.summary,
            turns=[InterviewTurnDetail(turn_id=turn.id, question_order=turn.question_order, question=turn.question, answer=turn.answer, score=turn.score) for turn in turns],
        )

    async def answer_interview_question(self, session_id: int, payload: InterviewAnswerRequest) -> InterviewAnswerData:
        session = await InterviewSessionManager().query_by_id(session_id)
        if not session or session.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模拟面试不存在")
        turn = await InterviewTurnManager().query_one(
            conds=[InterviewTurnTable.id == payload.turn_id, InterviewTurnTable.session_id == session_id, InterviewTurnTable.deleted_at.is_(None)]
        )
        if not turn:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="面试题目不存在")
        score = self.score_answer(payload.answer)
        feedback = self.build_interview_feedback(payload.answer, score)
        weak_points: list[str] = []
        if score < 70:
            weak_points.append("回答缺少具体指标和案例支撑")
            await self.upsert_weak_point(scene_id=session.scene_id, concept="面试回答缺少结构化表达", source_type="interview", mastery_level="weak")
        await InterviewTurnManager().update(
            values={"answer": payload.answer, "score": score, "feedback": feedback.model_dump()},
            conds=[InterviewTurnTable.id == turn.id],
        )
        answered_scores = await InterviewTurnManager().query_all(
            cols=[InterviewTurnTable.score],
            conds=[InterviewTurnTable.session_id == session_id, InterviewTurnTable.score.is_not(None), InterviewTurnTable.deleted_at.is_(None)],
            flat=True,
        )
        overall_score = round(sum(answered_scores) / len(answered_scores), 1) if answered_scores else score
        session_status = "completed" if len(answered_scores) >= 3 else "in_progress"
        await InterviewSessionManager().update(
            values={"overall_score": overall_score, "summary": "面试表现整体稳定，建议继续补强回答中的业务结果和量化指标。", "status": session_status},
            conds=[InterviewSessionTable.id == session_id],
        )
        return InterviewAnswerData(
            session_id=session_id,
            turn_id=turn.id,
            score=score,
            feedback=feedback,
            weak_points=weak_points,
            session_status=session_status,
        )
