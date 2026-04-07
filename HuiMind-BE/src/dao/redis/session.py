"""Redis session helpers.

该模块提供 Redis 会话相关的辅助函数。
注意：问答历史现在由 LangGraph Checkpointer 自动管理，不再使用此模块。
"""

import redis.asyncio as redis

from src import settings

_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password or None,
    decode_responses=True,
)


# 问答历史功能已迁移到 LangGraph Checkpointer
# 保留 _client 供其他模块使用

