"""LangGraph Checkpointer with TTL refresh support.

该模块提供 Checkpointer 单例，用于管理 Agent 的短期记忆。
"""

from langgraph.checkpoint.memory import InMemorySaver

_checkpointer = None


async def get_checkpointer():
    """获取 Checkpointer 单例。

    Returns:
        InMemorySaver 实例。
    """
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = InMemorySaver()
    return _checkpointer
