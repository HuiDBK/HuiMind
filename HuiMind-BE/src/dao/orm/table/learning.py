"""ORM tables for HuiMind API domains."""

from datetime import datetime

from sqlalchemy import JSON, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from py_tools.connections.db.mysql import BaseOrmTableWithTS


class SceneTable(BaseOrmTableWithTS):
    __tablename__ = "scene"

    scene_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, comment="场景编码")
    name: Mapped[str] = mapped_column(String(64), comment="场景名称")
    description: Mapped[str] = mapped_column(String(255), comment="场景描述")
    enabled_tools: Mapped[list[str]] = mapped_column(JSON, default=list, comment="启用工具列表")


class DocumentTable(BaseOrmTableWithTS):
    __tablename__ = "document"

    scene_id: Mapped[str] = mapped_column(String(32), index=True, comment="场景编码")
    doc_type: Mapped[str] = mapped_column(String(32), index=True, comment="资料类型")
    filename: Mapped[str] = mapped_column(String(255), comment="文件名")
    status: Mapped[str] = mapped_column(String(32), default="ready", comment="资料状态")
    summary: Mapped[str] = mapped_column(String(500), default="", comment="资料摘要")
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="来源链接")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="内容全文")


class BuddyProfileTable(BaseOrmTableWithTS):
    __tablename__ = "buddy_profile"

    user_id: Mapped[int] = mapped_column(Integer, index=True, comment="用户ID")
    name: Mapped[str] = mapped_column(String(64), comment="搭子名称")
    persona: Mapped[str] = mapped_column(String(32), comment="搭子人格")
    memory_summary: Mapped[str] = mapped_column(String(500), default="", comment="记忆摘要")
    last_interaction_at: Mapped[datetime | None] = mapped_column(nullable=True, comment="最后互动时间")


class QaRecordTable(BaseOrmTableWithTS):
    __tablename__ = "qa_record"

    scene_id: Mapped[str] = mapped_column(String(32), index=True, comment="场景编码")
    session_id: Mapped[int] = mapped_column(Integer, index=True, default=1, comment="会话ID")
    question: Mapped[str] = mapped_column(Text, comment="问题")
    answer: Mapped[str] = mapped_column(Text, comment="回答")
    citations: Mapped[list[dict]] = mapped_column(JSON, default=list, comment="引用信息")
    insufficient_context: Mapped[int] = mapped_column(Integer, default=0, comment="上下文是否不足")


class WeakPointTable(BaseOrmTableWithTS):
    __tablename__ = "weak_point"

    scene_id: Mapped[str] = mapped_column(String(32), index=True, comment="场景编码")
    concept: Mapped[str] = mapped_column(String(255), comment="薄弱点概念")
    source_type: Mapped[str] = mapped_column(String(32), comment="来源类型")
    wrong_count: Mapped[int] = mapped_column(Integer, default=0, comment="错误次数")
    correct_rate: Mapped[float] = mapped_column(Float, default=0, comment="正确率")
    mastery_level: Mapped[str] = mapped_column(String(32), default="reviewing", comment="掌握程度")
    next_review_at: Mapped[datetime] = mapped_column(comment="下次复习时间")


class ReviewTaskTable(BaseOrmTableWithTS):
    __tablename__ = "review_task"

    scene_id: Mapped[str] = mapped_column(String(32), index=True, comment="场景编码")
    concept: Mapped[str] = mapped_column(String(255), comment="复习概念")
    due_at: Mapped[datetime] = mapped_column(comment="到期时间")
    status: Mapped[str] = mapped_column(String(32), default="pending", comment="任务状态")


class ResumeDiagnosisTable(BaseOrmTableWithTS):
    __tablename__ = "resume_diagnosis"

    scene_id: Mapped[str] = mapped_column(String(32), index=True, comment="场景编码")
    resume_doc_id: Mapped[int] = mapped_column(Integer, index=True, comment="简历文档ID")
    jd_doc_id: Mapped[int] = mapped_column(Integer, index=True, comment="JD 文档ID")
    match_score: Mapped[float] = mapped_column(Float, comment="匹配分")
    matched_keywords: Mapped[list[str]] = mapped_column(JSON, default=list, comment="命中关键词")
    missing_keywords: Mapped[list[str]] = mapped_column(JSON, default=list, comment="缺失关键词")
    risky_phrases: Mapped[list[dict]] = mapped_column(JSON, default=list, comment="风险表达")
    rewrite_suggestions: Mapped[list[dict]] = mapped_column(JSON, default=list, comment="重写建议")
    summary: Mapped[str] = mapped_column(String(500), comment="诊断总结")


class InterviewSessionTable(BaseOrmTableWithTS):
    __tablename__ = "interview_session"

    scene_id: Mapped[str] = mapped_column(String(32), index=True, comment="场景编码")
    jd_doc_id: Mapped[int] = mapped_column(Integer, index=True, comment="JD 文档ID")
    mode: Mapped[str] = mapped_column(String(32), default="standard", comment="面试模式")
    status: Mapped[str] = mapped_column(String(32), default="in_progress", comment="会话状态")
    overall_score: Mapped[float] = mapped_column(Float, default=0, comment="整体得分")
    summary: Mapped[str] = mapped_column(String(500), default="", comment="会话总结")


class InterviewTurnTable(BaseOrmTableWithTS):
    __tablename__ = "interview_turn"

    session_id: Mapped[int] = mapped_column(Integer, index=True, comment="会话ID")
    question_order: Mapped[int] = mapped_column(Integer, comment="问题顺序")
    question: Mapped[str] = mapped_column(Text, comment="问题内容")
    answer: Mapped[str | None] = mapped_column(Text, nullable=True, comment="回答内容")
    score: Mapped[float | None] = mapped_column(Float, nullable=True, comment="本轮评分")
    feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="反馈详情")
