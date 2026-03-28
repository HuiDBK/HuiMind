"""基于 LangGraph 的学习 Agent 实现。

该模块使用 LangGraph 构建 ReAct 模式的 Agent，支持：
- 工具调用与多轮推理
- 流式输出
- 迭代次数限制防止无限循环
"""

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from loguru import logger

from src.agents.agent_prompt import build_general_prompt, build_system_prompt
from src.agents.agent_tools import build_tools_for_scene
from src.dao.orm.table import SceneTable
from src.services.llm import LLMConfig, LLMProvider, LLMService


class AgentState(TypedDict):
    """Agent 状态定义。

    Attributes:
        messages: 消息历史，自动合并。
        user_id: 用户 ID。
        scene: 场景配置对象。
        persona: AI 人设风格。
        tools_used: 本轮使用的工具名称列表。
        iteration_count: 当前迭代次数，用于防止无限循环。
    """

    messages: Annotated[list[BaseMessage], add_messages]
    user_id: int
    scene: SceneTable | None
    persona: str
    tools_used: list[str]
    iteration_count: int


def make_agent_node(llm_with_tools):
    """创建 Agent 推理节点。

    Args:
        llm_with_tools: 绑定了工具的 LLM 实例。

    Returns:
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
            scene = state.get("scene")
            persona = state.get("persona", "严师型")
            if scene is not None:
                system_content = build_system_prompt(scene, persona)
            else:
                system_content = build_general_prompt(persona)
            messages = [SystemMessage(content=system_content)] + messages

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


def build_study_agent(user_id: str, scene: SceneTable | None, persona: str = "严师型"):
    """构建学习 Agent 图。

    Args:
        user_id: 用户 ID。
        scene: 场景配置对象，为 None 时使用通用场景。
        persona: AI 人设风格，默认"严师型"。

    Returns:
        编译后的 LangGraph 图实例。
    """
    tools_enabled = (scene.tools_enabled if scene else []) or ["qa", "quiz", "memory"]
    tools = build_tools_for_scene(user_id, scene.scene_id if scene else "general", tools_enabled)

    llm = LLMService.get(
        provider=LLMProvider.OPENAI,
        config=LLMConfig(temperature=0.3, streaming=True),
    )
    llm_with_tools = llm.bind_tools(tools)

    graph = StateGraph(AgentState)
    graph.add_node("agent", make_agent_node(llm_with_tools))
    graph.add_node("tools", make_tool_node(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")

    compiled_graph = graph.compile()
    logger.info(
        f"[Agent] Built for user={user_id[:8] if len(user_id) > 8 else user_id} "
        f"scene={scene.name if scene else 'general'} tools={[t.name for t in tools]}"
    )
    return compiled_graph


async def run_agent_stream(graph, user_id: int, scene: SceneTable | None, question: str, persona: str = "严师型"):
    """流式运行 Agent 并 yield 事件。

    Args:
        graph: 编译后的 LangGraph 图实例。
        user_id: 用户 ID。
        scene: 场景配置对象。
        question: 用户问题。
        persona: AI 人设风格。

    Yields:
        事件字典，包含 type 和 content 等字段。
    """
    initial_state: AgentState = {
        "messages": [HumanMessage(content=question)],
        "user_id": user_id,
        "scene": scene,
        "persona": persona,
        "tools_used": [],
        "iteration_count": 0,
    }

    yield {"type": "status", "content": "开始处理请求..."}

    async for event in graph.astream_events(initial_state, version="v2"):
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
