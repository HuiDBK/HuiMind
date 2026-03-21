import json
from collections.abc import Awaitable, Callable

from langchain_core.tools import Tool


TOOL_SPECS = {
    "kb_search_tool": "检索用户知识库（RAG），返回片段与引用来源。",
    "generate_quiz_tool": "从知识库内容生成练习题（含答案与解析）。",
    "update_weakness_tool": "更新薄弱点画像（识别知识点并记录到薄弱点）。",
    "schedule_review_tool": "将某个知识点加入复习计划并生成艾宾浩斯节奏。",
    "evaluate_rubric_tool": "按场景评分规则对文本进行评分与改进建议。",
    "web_search_tool": "补充外部最新资料（MVP 可返回引导信息）。",
    "memory_tool": "查询用户长期记忆（薄弱点、复习任务、历史对话摘要）。",
}


NAME_ALIASES = {
    "search_knowledge": "kb_search_tool",
    "kb_search": "kb_search_tool",
    "generate_quiz": "generate_quiz_tool",
    "quiz": "generate_quiz_tool",
    "update_weakness": "update_weakness_tool",
    "schedule_review": "schedule_review_tool",
    "review": "schedule_review_tool",
    "rubric_evaluate": "evaluate_rubric_tool",
    "evaluate_rubric": "evaluate_rubric_tool",
    "web_search": "web_search_tool",
    "crawler": "web_search_tool",
    "memory": "memory_tool",
}


def build_agent_tools(
    *,
    service,
    scene_id: str,
    enabled_tools: list[str] | None,
    eval_rubric: dict | None,
) -> list[Tool]:
    enabled = set(enabled_tools or [])
    allow_all = not enabled
    resolved = {NAME_ALIASES.get(t, t) for t in enabled}

    def allow(name: str) -> bool:
        return allow_all or name in resolved

    tools: list[Tool] = []

    def normalize_input(raw) -> str:
        if raw is None:
            return ""
        if isinstance(raw, str):
            return raw
        if isinstance(raw, dict):
            for key in ("__arg1", "input", "query", "text", "concept", "content"):
                v = raw.get(key)
                if isinstance(v, str) and v.strip():
                    return v
            return json.dumps(raw, ensure_ascii=False)
        return str(raw)

    def _tool_async(name: str, desc: str, coro: Callable[[str], Awaitable[str]]) -> None:
        tools.append(Tool(name=name, func=None, coroutine=coro, description=desc))

    def _tool_sync(name: str, desc: str, fn: Callable[[str], str]) -> None:
        tools.append(Tool(name=name, func=fn, description=desc))

    if allow("kb_search_tool"):
        _tool_async(
            "kb_search_tool",
            TOOL_SPECS["kb_search_tool"],
            lambda s: service.kb_search(scene_id=scene_id, query=normalize_input(s)),
        )
    if allow("generate_quiz_tool"):
        _tool_async(
            "generate_quiz_tool",
            TOOL_SPECS["generate_quiz_tool"],
            lambda s: service.generate_quiz(scene_id=scene_id, raw_input=normalize_input(s)),
        )
    if allow("update_weakness_tool"):
        _tool_async(
            "update_weakness_tool",
            TOOL_SPECS["update_weakness_tool"],
            lambda s: service.update_weakness(scene_id=scene_id, raw_input=normalize_input(s)),
        )
    if allow("schedule_review_tool"):
        _tool_async(
            "schedule_review_tool",
            TOOL_SPECS["schedule_review_tool"],
            lambda s: service.schedule_review(scene_id=scene_id, concept=normalize_input(s)),
        )
    if allow("evaluate_rubric_tool"):
        rubric = eval_rubric or {}
        _tool_async(
            "evaluate_rubric_tool",
            TOOL_SPECS["evaluate_rubric_tool"],
            lambda s: service.evaluate_rubric(scene_id=scene_id, eval_rubric=rubric, raw_input=normalize_input(s)),
        )
    if allow("web_search_tool"):
        _tool_sync(
            "web_search_tool",
            TOOL_SPECS["web_search_tool"],
            lambda s: service.web_search(raw_input=normalize_input(s)),
        )
    if allow("memory_tool"):
        _tool_async(
            "memory_tool",
            TOOL_SPECS["memory_tool"],
            lambda s: service.query_memory(scene_id=scene_id, query=normalize_input(s)),
        )

    return tools
