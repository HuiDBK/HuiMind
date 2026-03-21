"""Redis session helpers."""

import json

import redis.asyncio as redis

from src import settings

_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password or None,
    decode_responses=True,
)


def _qa_key(*, user_id: int, scene_id: str, session_id: int) -> str:
    return f"session:qa:{user_id}:{scene_id}:{session_id}"


async def append_qa_message(*, user_id: int, scene_id: str, session_id: int, role: str, content: str) -> None:
    key = _qa_key(user_id=user_id, scene_id=scene_id, session_id=session_id)
    await _client.rpush(key, json.dumps({"role": role, "content": content}, ensure_ascii=False))
    await _client.expire(key, 60 * 60 * 24 * 14)


async def get_qa_history(*, user_id: int, scene_id: str, session_id: int, limit: int = 10) -> list[dict]:
    key = _qa_key(user_id=user_id, scene_id=scene_id, session_id=session_id)
    raw = await _client.lrange(key, max(0, -limit * 2), -1)
    items: list[dict] = []
    for entry in raw:
        try:
            items.append(json.loads(entry))
        except Exception:
            continue
    return items

