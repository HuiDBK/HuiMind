"""基于 LangGraph 的学习 Agent 实现。

该模块使用 LangGraph 构建 ReAct 模式的 Agent，支持：
- 工具调用与多轮推理
- 流式输出
- 迭代次数限制防止无限循环
- 短期记忆管理（Checkpointer）
- 消息压缩机制（pre_model_hook）
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from typing_extensions import NotRequired

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from loguru import logger

from src.agents.agent_prompt import build_general_prompt, build_system_prompt
from src.agents.agent_tools import build_agent_tools
from src.agents.message_compression import compress_messages
from src.dao.orm.table import SceneTable
from src.dao.redis.checkpointer import get_checkpointer
from src.services.llm import LLMConfig, LLMProvider, LLMService


class AgentState(TypedDict):
    """Agent 状态定义。

    Attributes:
        messages: 消息历史，自动合并。
        user_id: 用户 ID。
        scene_id: 场景 ID（用于 Checkpointer 序列化）。
        persona: AI 人设风格。
        system_prompt: 本次会话的 System Prompt（可序列化，避免节点内查库/拼装）。
        tools_used: 本轮使用的工具名称列表。
        iteration_count: 当前迭代次数，用于防止无限循环。
    """

    messages: Annotated[list[BaseMessage], add_messages]
    user_id: int
    scene_id: str | None
    persona: str
    system_prompt: NotRequired[str]
    tools_used: list[str]
    iteration_count: int


def make_agent_node(llm_with_tools, llm):
    """创建 Agent 推理节点。

    Args:
        llm_with_tools: 绑定了工具的 LLM 实例。
        llm: 原始 LLM 实例（用于压缩摘要）。

    Returns:·
        Agent 节点函数。
    """

    async def agent_node(state: AgentState) -> dict:
        """执行一轮 Agent 推理。

        Args:
            state: 当前 Agent 状态。

        Returns:
            更新后的状态字典。
        """
        if state["iteration_count"] > 10:
            logger.warning(f"[Agent] max iterations reached for user {state['user_id']}")
            return {
                "messages": state["messages"] + [AIMessage(content="（已达到最大推理轮次，直接给出当前结论）")],
                "iteration_count": state["iteration_count"] + 1,
            }

        messages = list(state["messages"])
        if not messages or not isinstance(messages[0], SystemMessage):
            system_content = state.get("system_prompt") or build_general_prompt(state.get("persona", "严师型"))
            messages = [SystemMessage(content=system_content)] + messages
        else:
            # 保持 system prompt 为最新（避免历史里固化旧提示）
            system_content = state.get("system_prompt")
            if system_content:
                messages[0] = SystemMessage(content=system_content)

        # pre_model_hook: 在调用 LLM 前压缩消息历史
        before_len = len(messages)
        compressed = await compress_messages({"messages": messages}, llm)
        messages = compressed.get("messages", messages)
        after_len = len(messages)
        if after_len != before_len:
            logger.info(f"[Agent][Compression] messages {before_len} -> {after_len}")

        response = await llm_with_tools.ainvoke(messages)
        tool_calls_count = len(getattr(response, "tool_calls", []))
        logger.info(f"[Agent] iter={state['iteration_count'] + 1} tool_calls={tool_calls_count}")

        return {
            "messages": [response],
            "iteration_count": state["iteration_count"] + 1,
        }

    return agent_node


def make_tool_node(tools):
    """创建工具执行节点。

    Args:
        tools: 工具列表。

    Returns:
        工具执行节点函数。
    """
    tool_node = ToolNode(tools)

    async def tool_executor(state: AgentState) -> dict:
        """执行工具调用。

        Args:
            state: 当前 Agent 状态。

        Returns:
            更新后的状态字典。
        """
        last = state["messages"][-1]
        names = [tc["name"] for tc in getattr(last, "tool_calls", [])]
        logger.info(f"[Agent] executing tools: {names}")

        result = await tool_node.ainvoke(state)
        return {
            "messages": result.get("messages", []),
            "tools_used": state.get("tools_used", []) + names,
        }

    return tool_executor


def should_continue(state: AgentState) -> str:
    """路由函数：决定下一步走工具节点还是结束。

    Args:
        state: 当前 Agent 状态。

    Returns:
        "tools" 表示继续执行工具，"end" 表示结束。
    """
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "end"


async def build_study_agent(
    user_id: str,
    scene: SceneTable | None,
    persona: str = "严师型",
):
    """构建学习 Agent 图。

    Args:
        user_id: 用户 ID。
        scene: 场景配置对象，为 None 时使用通用场景。
        persona: AI 人设风格，默认"严师型"。

    Returns:
        编译后的 LangGraph 图实例（带 Checkpointer）。
    """
    tools_enabled = (scene.enabled_tools if scene else []) or ["qa", "quiz", "update_weakness", "query_memory"]
    eval_rubric = (scene.eval_rubric if scene else {}) or {}
    tools = build_agent_tools(
        scene_id=scene.scene_id if scene else "general",
        enabled_tools=tools_enabled,
        eval_rubric=eval_rubric,
    )

    llm = LLMService.get(
        provider=LLMProvider.OPENAI,
        config=LLMConfig(temperature=0.3, streaming=True),
    )
    llm_with_tools = llm.bind_tools(tools)

    graph = StateGraph(AgentState)
    graph.add_node("agent", make_agent_node(llm_with_tools, llm))
    graph.add_node("tools", make_tool_node(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")

    # 集成 Redis Checkpointer
    checkpointer = await get_checkpointer()
    compiled_graph = graph.compile(checkpointer=checkpointer)

    logger.info(
        f"[Agent] Built for user={user_id[:8] if len(user_id) > 8 else user_id} "
        f"scene={scene.name if scene else 'general'} tools={[t.name for t in tools]}"
    )
    return compiled_graph

async def run_agent_stream(
    graph,
    user_id: int,
    scene: SceneTable | None,
    question: str,
    session_id: str = "default",
    persona: str = "严师型",
    system_prompt: str | None = None,
):
    """流式运行 Agent 并 yield 事件。

    Args:
        graph: 编译后的 LangGraph 图实例。
        user_id: 用户 ID。
        scene: 场景配置对象。
        question: 用户问题。
        session_id: 会话 ID，默认 "default"。
        persona: AI 人设风格。

    Yields:
        事件字典，包含 type 和 content 等字段。
    """
    scene_id = scene.scene_id if scene else "general"

    # thread_id 格式: {user_id}:{scene_id}:{session_id}
    thread_id = f"{user_id}:{scene_id}:{session_id}"
    config = {"configurable": {"thread_id": thread_id}}

    # 历史由 Checkpointer 自动恢复，无需手动加载
    initial_state: AgentState = {
        "messages": [HumanMessage(content=question)],
        "user_id": user_id,
        "scene_id": scene.scene_id if scene else "general",
        "persona": persona,
        "system_prompt": system_prompt
        or (build_system_prompt(scene=scene, persona=persona, context=None) if scene else build_general_prompt(persona=persona, context=None)),
        "tools_used": [],
        "iteration_count": 0,
    }

    yield {"type": "status", "content": "开始处理请求..."}

    async for event in graph.astream_events(initial_state, config, version="v2"):
        evt = event.get("event")
        name = event.get("name")
        data = event.get("data") or {}

        if evt == "on_tool_start":
            yield {
                "type": "tool_start",
                "tool_name": name,
                "input": data.get("input"),
            }
        elif evt == "on_tool_end":
            output = data.get("output")
            if not isinstance(output, str):
                output = getattr(output, "content", str(output))
            yield {
                "type": "tool_end",
                "tool_name": name,
                "output": output[:2000] if len(str(output)) > 2000 else output,
            }
        elif evt == "on_chat_model_stream":
            chunk = data.get("chunk")
            piece = getattr(chunk, "content", None)
            if piece:
                yield {"type": "token", "content": piece}
        elif evt == "on_chain_end" and name == "LangGraph":
            output = data.get("output", {})
            messages = output.get("messages", [])
            if messages:
                last_msg = messages[-1]
                content = getattr(last_msg, "content", "")
                yield {
                    "type": "final",
                    "content": content,
                    "tools_used": output.get("tools_used", []),
                }
