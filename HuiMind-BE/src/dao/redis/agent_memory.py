"""自管 Agent 线程态记忆（Redis）。

该模块用于在不依赖 LangGraph Redis checkpointer 的前提下，让对话在服务重启后可恢复。

设计原则：
- 只保存“可控且高信噪比”的信息：历史摘要 + 最近少量消息
- 存储结构完全由业务方定义，避免第三方库版本冲突
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Literal

import redis.asyncio as redis
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from loguru import logger

from src import settings


@dataclass
class ThreadMemory:
    """线程态记忆快照。

    Attributes:
        summary: 历史摘要（100~200 字左右，避免膨胀）。
        recent_messages: 最近 N 条消息（用于恢复短期上下文）。
        updated_at_ms: 最后更新时间戳（毫秒）。
    """

    summary: str = ""
    recent_messages: list[dict[str, Any]] | None = None
    updated_at_ms: int = 0


_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password or None,
    decode_responses=True,
)


def _key(*, user_id: int, scene_id: str, session_id: str) -> str:
    return f"agent:thread:{user_id}:{scene_id}:{session_id}"


def _msg_to_record(msg: BaseMessage) -> dict[str, Any] | None:
    if isinstance(msg, HumanMessage):
        role: Literal["human"] = "human"
        return {"role": role, "content": msg.content}
    if isinstance(msg, AIMessage):
        role: Literal["ai"] = "ai"
        return {"role": role, "content": msg.content}
    if isinstance(msg, ToolMessage):
        role: Literal["tool"] = "tool"
        return {"role": role, "content": getattr(msg, "content", ""), "name": getattr(msg, "name", None)}
    return None


def _records_to_text(records: list[dict[str, Any]]) -> str:
    """把最近消息拼成紧凑可读的文本，供注入 prompt 用。"""
    lines: list[str] = []
    for r in records:
        role = r.get("role")
        content = (r.get("content") or "").strip()
        if not content:
            continue
        if role == "human":
            lines.append(f"用户：{content}")
        elif role == "ai":
            lines.append(f"助手：{content}")
        elif role == "tool":
            name = r.get("name") or "tool"
            lines.append(f"[工具:{name}] {content}")
    return "\n".join(lines)


async def load_thread_memory(
    *,
    user_id: int,
    scene_id: str,
    session_id: str,
) -> ThreadMemory:
    """加载线程态记忆。

    Returns:
        ThreadMemory: 若无数据则返回空对象。
    """
    k = _key(user_id=user_id, scene_id=scene_id, session_id=session_id)
    raw = await _client.get(k)
    if not raw:
        return ThreadMemory(recent_messages=[], updated_at_ms=0)
    try:
        obj = json.loads(raw)
        return ThreadMemory(
            summary=str(obj.get("summary") or ""),
            recent_messages=list(obj.get("recent_messages") or []),
            updated_at_ms=int(obj.get("updated_at_ms") or 0),
        )
    except Exception as exc:
        logger.warning(f"[AgentMemory] load failed key={k}: {exc}")
        return ThreadMemory(recent_messages=[], updated_at_ms=0)


async def save_thread_memory(
    *,
    user_id: int,
    scene_id: str,
    session_id: str,
    messages: list[BaseMessage],
    summary: str = "",
    ttl_seconds: int = 60 * 60 * 24 * 14,
    keep_recent: int = 20,
) -> None:
    """写回线程态记忆。

    Args:
        messages: 完整消息列表（会截取最近 keep_recent 条持久化）。
        summary: 外部生成的历史摘要；为空则只存 recent_messages。
    """
    k = _key(user_id=user_id, scene_id=scene_id, session_id=session_id)

    records: list[dict[str, Any]] = []
    for m in messages[-keep_recent:]:
        rec = _msg_to_record(m)
        if rec:
            records.append(rec)

    payload = ThreadMemory(
        summary=(summary or "")[:400],
        recent_messages=records,
        updated_at_ms=int(time.time() * 1000),
    )

    await _client.set(k, json.dumps(asdict(payload), ensure_ascii=False), ex=ttl_seconds)


def build_memory_summary_for_prompt(mem: ThreadMemory) -> str:
    """把 ThreadMemory 转成适合 Layer4 注入的摘要文本。"""
    parts: list[str] = []
    if mem.summary:
        parts.append(mem.summary.strip()[:240])
    if mem.recent_messages:
        recent_text = _records_to_text(mem.recent_messages)
        if recent_text:
            parts.append(recent_text[:800])
    return "\n".join([p for p in parts if p]).strip()

