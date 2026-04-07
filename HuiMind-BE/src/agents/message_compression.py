"""消息压缩模块。

提供两种压缩策略：
1. Token 超 65% 压缩：触发 LLM 摘要
2. 最近 50 轮对话压缩：保留最近 N 轮

通过 LangGraph 的 pre_model_hook 在每次调用 LLM 前执行。
"""

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from loguru import logger

MAX_CONTEXT_TOKENS = 128000
MAX_HISTORY_TURNS = 50
TOKEN_THRESHOLD = 0.65


def count_tokens(messages: list[BaseMessage]) -> int:
    """估算消息的 Token 数。

    Args:
        messages: 消息列表。

    Returns:
        Token 数估算值。
    """
    total = 0
    for msg in messages:
        content = getattr(msg, "content", "") or ""
        total += len(content) // 4
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                total += len(str(tc)) // 4
    return total


def compress_by_turns(messages: list[BaseMessage], max_turns: int = MAX_HISTORY_TURNS) -> list[BaseMessage]:
    """保留最近 N 轮对话。

    Args:
        messages: 消息列表。
        max_turns: 最大保留轮数。

    Returns:
        压缩后的消息列表。
    """
    if len(messages) <= max_turns * 2:
        return messages

    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]

    recent = other_msgs[-max_turns * 2:]

    logger.info(f"[Compression] Truncated to {len(recent)} messages from {len(other_msgs)}")
    return system_msgs + recent


async def summarize_messages(messages: list[BaseMessage], llm) -> str:
    """使用 LLM 生成摘要。

    Args:
        messages: 需要摘要的消息列表。
        llm: LLM 实例。

    Returns:
        摘要文本。
    """
    topics = []
    for msg in messages:
        if isinstance(msg, HumanMessage) and msg.content:
            topic = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            topics.append(topic)

    if not topics:
        return "无历史对话"

    prompt = f"请用 100 字以内总结以下对话的主题：\n{chr(10).join(topics[:10])}"
    try:
        response = await llm.ainvoke(prompt)
        return getattr(response, "content", f"之前讨论了: {', '.join(topics[:3])}")
    except Exception as e:
        logger.error(f"[Compression] Summarization failed: {e}")
        return f"之前讨论了: {', '.join(topics[:3])}"


async def compress_by_token_ratio(
    messages: list[BaseMessage],
    llm,
    threshold: float = TOKEN_THRESHOLD,
    max_tokens: int = MAX_CONTEXT_TOKENS,
) -> list[BaseMessage]:
    """当 Token 超过阈值时触发压缩。

    Args:
        messages: 消息列表。
        llm: LLM 实例。
        threshold: 压缩阈值。
        max_tokens: 模型最大 Token 数。

    Returns:
        压缩后的消息列表。
    """
    current_tokens = count_tokens(messages)
    max_allowed = int(max_tokens * threshold)

    if current_tokens <= max_allowed:
        return messages

    logger.info(f"[Compression] Token {current_tokens} > {max_allowed}, triggering compression")

    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    recent_msgs = [m for m in messages if m not in system_msgs][-20:]

    early_msgs = [m for m in messages if m not in system_msgs and m not in recent_msgs]
    summary = await summarize_messages(early_msgs, llm)

    return system_msgs + [SystemMessage(content=f"[历史摘要]\n{summary}")] + recent_msgs


async def compress_messages(state: dict, llm) -> dict:
    """pre_model_hook：在调用 LLM 前压缩消息历史。

    两种压缩策略依次执行：
    1. 最近 50 轮对话压缩
    2. Token 超 65% 压缩

    Args:
        state: Agent 状态字典。
        llm: LLM 实例。

    Returns:
        更新后的状态字典。
    """
    messages = state.get("messages", [])
    if not messages:
        return {"messages": []}

    # 检查是否已经压缩过（避免重复压缩）
    has_compressed = any(
        isinstance(msg, SystemMessage) and "[历史摘要]" in getattr(msg, "content", "")
        for msg in messages
    )

    if has_compressed:
        logger.info("[Compression] Already compressed, skipping")
        return {"messages": messages}

    messages = compress_by_turns(messages, MAX_HISTORY_TURNS)
    messages = await compress_by_token_ratio(messages, llm, TOKEN_THRESHOLD, MAX_CONTEXT_TOKENS)

    return {"messages": messages}
