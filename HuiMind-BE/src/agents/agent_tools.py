"""Agent 可调用的工具集。

每个工具都是 LLM 可以"自主决定要不要用"的能力。
工具设计原则：描述要清晰，让 LLM 能准确判断何时该用哪个。

架构说明：
    巅层工具直接依赖 Manager 层（数据访问层），不依赖 Service 层。
    工具使用异步函数，LangChain 会自动处理异步调用。
"""

import json
from datetime import datetime, timedelta

from langchain_core.tools import tool
from loguru import logger

from src.dao.orm.manager.review import ReviewTaskManager, WeakPointManager
from src.dao.orm.table import ReviewTaskTable, WeakPointTable
from src.services.base import now_ts
from src.services.rag import RAGService
from src.services.llm import LLMConfig, LLMProvider, LLMService
from src.domain.agent_ops import kb_search as domain_kb_search


# Query 分类映射
MEMORY_QUERY_PATTERNS = {
    "weakness": ["薄弱", "弱点", "错误", "不会", "不懂", "掌握", "学得不好", "哪块不好"],
    "review": ["复习", "复盘", "待做", "任务", "计划", "到期", "该复习"],
    "status": ["状态", "进度", "情况", "学得怎样", "如何", "怎么样"],
}


def classify_query(query: str) -> str:
    """分类查询意图。

    Args:
        query: 用户查询内容。

    Returns:
        查询类别：weakness/review/status/all
    """
    query_lower = query.lower()
    for category, patterns in MEMORY_QUERY_PATTERNS.items():
        if any(p in query_lower for p in patterns):
            return category
    return "all"


def make_search_knowledge_tool(scene_id: str):
    """创建知识库检索工具。

    Args:
        scene_id: 场景 ID。

    Returns:
        LangChain 工具实例。
    """
    @tool
    async def search_knowledge(query: str) -> str:
        """在知识库中检索相关内容。

        当用户提问涉及具体知识点、概念解释、真题解析时使用。
        如果问题是闲聊、打招呼、或明显不需要查资料时，不要调用此工具。

        Args:
            query: 检索查询词，应提炼为关键概念，保留专业术语，不超过50字。

        Returns:
            检索到的相关文档片段，包含来源标注。
        """
        try:
            result = await domain_kb_search(scene_id=scene_id, query=query, k=6, citations_map=None)
            logger.info(f"[Tool:search_knowledge] query='{query}'")
            return result
        except Exception as e:
            logger.error(f"[Tool:search_knowledge] error: {e}")
            return f"知识库检索失败：{str(e)}"

    return search_knowledge


def make_generate_quiz_tool(scene_id: str):
    """创建出题测试工具。

    Args:
        scene_id: 场景 ID。

    Returns:
        LangChain 工具实例。
    """
    llm = LLMService.get(provider=LLMProvider.OPENAI, config=LLMConfig(temperature=0.3))
    search_tool = make_search_knowledge_tool(scene_id)

    @tool
    async def generate_quiz(knowledge_point: str, difficulty: str = "medium") -> str:
        """根据知识点生成练习题。

        当以下情况时主动调用：
        1. 用户刚问完某个知识点，适合趁热出题巩固
        2. 用户明确要求"出题"、"考考我"、"测试一下"
        3. 检测到用户对某概念理解不够透彻时

        Args:
            knowledge_point: 要出题的知识点。
            difficulty: 难度 easy/medium/hard，默认 medium。

        Returns:
            格式化的题目（含选项和提示）。
        """
        try:
            kb_result = await search_tool.ainvoke(knowledge_point)
            kb_obj = json.loads(kb_result) if kb_result.startswith("{") else {"snippets": []}
            context = "\n\n".join([s.get("content", "") for s in kb_obj.get("snippets", [])])[:6000]

            prompt = (
                "你是学习助手，请基于给定资料内容生成练习题。\n"
                f"题型偏好：{difficulty}\n"
                "要求：输出 JSON，包含 questions 数组，每题含 question, options, answer, explanation。\n"
                f"资料内容：\n{context}\n"
                f"知识点：{knowledge_point}\n"
            )
            resp = await llm.ainvoke(prompt)
            logger.info(f"[Tool:generate_quiz] kp='{knowledge_point}'")
            return getattr(resp, "content", str(resp))
        except Exception as e:
            logger.error(f"[Tool:generate_quiz] error: {e}")
            return f"出题失败：{str(e)}"

    return generate_quiz


def make_update_weakness_tool(scene_id: str):
    """创建更新薄弱点工具。

    Args:
        scene_id: 场景 ID。

    Returns:
        LangChain 工具实例。
    """

    @tool
    async def update_weakness_profile(concept: str, is_correct: bool = True) -> str:
        """记录知识点掌握情况到学习画像。

        调用时机：
        1. 用户回答了一道题（无论对错）
        2. 用户对某个概念反复提问（说明没掌握）
        3. 用户明确表示"这个我不会"

        Args:
            concept: 知识点名称。
            is_correct: 用户是否回答正确，默认 True。

        Returns:
            更新结果描述。
        """
        try:
            row = await WeakPointManager().query_one(
                conds=[WeakPointTable.scene_id == scene_id, WeakPointTable.concept == concept, WeakPointTable.deleted_at.is_(None)]
            )
            if row:
                await WeakPointManager().update(
                    values={
                        "wrong_count": row.wrong_count + (0 if is_correct else 1),
                        "mastery_level": "reviewing" if is_correct else "weak",
                        "next_review_at": now_ts() + timedelta(days=1),
                    },
                    conds=[WeakPointTable.id == row.id],
                )
                return f"已更新「{concept}」掌握状态"
            else:
                await WeakPointManager().add(
                    {
                        "scene_id": scene_id,
                        "concept": concept,
                        "source_type": "agent",
                        "wrong_count": 0 if is_correct else 1,
                        "correct_rate": 100.0 if is_correct else 0.0,
                        "mastery_level": "reviewing" if is_correct else "weak",
                        "next_review_at": now_ts() + timedelta(days=1),
                    }
                )
                return f"已记录「{concept}」为{'已掌握' if is_correct else '薄弱点'}"
        except Exception as e:
            logger.error(f"[Tool:update_weakness] error: {e}")
            return f"记录失败：{str(e)}"

    return update_weakness_profile


def make_rubric_eval_tool(eval_rubric: dict):
    """创建评分工具。

    Args:
        eval_rubric: 评分规则配置。

    Returns:
        LangChain 工具实例。
    """
    llm = LLMService.get(provider=LLMProvider.OPENAI, config=LLMConfig(temperature=0.3))

    @tool
    async def rubric_evaluate(content: str, eval_type: str = "essay") -> str:
        """对用户提交的文章进行结构化评分。

        当检测到以下情况时调用：
        1. 用户发送了一段 200 字以上的连续文本
        2. 用户明确说"帮我看看这篇申论"、"批改一下"

        Args:
            content: 需要评分的文章内容。
            eval_type: "essay"（申论）或 "resume"（简历）。

        Returns:
            结构化评分结果。
        """
        try:
            rubric = json.dumps(eval_rubric or {}, ensure_ascii=False)
            prompt = (
                "你是学习助手，请按评分规则对用户文本进行评分并给出改进建议。\n"
                "输出要求：分项评分 + 总结 + 3 条可执行改进建议。\n"
                f"评分规则：{rubric}\n"
                f"用户文本：{content}\n"
            )
            resp = await llm.ainvoke(prompt)
            logger.info(f"[Tool:rubric_evaluate] eval_type='{eval_type}'")
            return getattr(resp, "content", str(resp))
        except Exception as e:
            logger.error(f"[Tool:rubric_evaluate] error: {e}")
            return f"批改失败：{str(e)}"

    return rubric_evaluate


def make_schedule_review_tool(scene_id: str):
    """创建复习调度工具。

    Args:
        scene_id: 场景 ID。

    Returns:
        LangChain 工具实例。
    """

    @tool
    async def schedule_review(concept: str, days_until_review: int = 1) -> str:
        """为知识点安排艾宾浩斯复习提醒。

        当以下情况时调用：
        1. 用户刚学完某个新知识点
        2. 用户说"帮我安排复习"、"记一下这个"

        Args:
            concept: 需要复习的知识点名称。
            days_until_review: 几天后复习，默认1天。

        Returns:
            安排结果描述。
        """
        try:
            due_at = now_ts() + timedelta(days=days_until_review)
            exists = await ReviewTaskManager().query_one(
                conds=[
                    ReviewTaskTable.scene_id == scene_id,
                    ReviewTaskTable.concept == concept,
                    ReviewTaskTable.status == "pending",
                    ReviewTaskTable.deleted_at.is_(None),
                ]
            )
            if not exists:
                await ReviewTaskManager().add(
                    {"scene_id": scene_id, "concept": concept, "due_at": due_at, "status": "pending"}
                )
                await WeakPointManager().add(
                    {
                        "scene_id": scene_id,
                        "concept": concept,
                        "source_type": "agent",
                        "wrong_count": 0,
                        "correct_rate": 100.0,
                        "mastery_level": "reviewing",
                        "next_review_at": due_at,
                    }
                )
            logger.info(f"[Tool:schedule_review] concept='{concept}'")
            return f"✅ 已为「{concept}」安排复习计划，下次复习时间：{due_at.strftime('%Y-%m-%d')}"
        except Exception as e:
            logger.error(f"[Tool:schedule_review] error: {e}")
            return f"安排复习失败：{str(e)}"

    return schedule_review


def make_web_search_tool():
    """创建联网搜索工具。

    Returns:
        LangChain 工具实例。
    """

    @tool
    def web_search(query: str) -> str:
        """当用户知识库中没有相关内容，且问题涉及时政热点、最新政策、近期新闻时使用。

        不要对知识库已有内容调用此工具。
        主要用于考公备考场景的时政热点补充。

        Args:
            query: 搜索关键词，应具体明确。

        Returns:
            搜索到的相关信息摘要。
        """
        logger.info(f"[Tool:web_search] query='{query}'")
        return (
            f"【联网搜索：{query}】\n"
            "注意：MVP 阶段联网搜索功能需配置 TAVILY_API_KEY。\n"
            "建议用户上传最新时政材料到知识库以获得更准确的内容。"
        )

    return web_search


def make_query_memory_tool(scene_id: str):
    """创建查询记忆工具。

    Args:
        scene_id: 场景 ID。

    Returns:
        LangChain 工具实例。
    """

    @tool
    async def query_memory(query: str) -> str:
        """查询用户的学习记忆（薄弱点、复习任务）。

        当用户问及学习状态、薄弱点、复习计划时调用。

        Args:
            query: 查询内容，如"我的薄弱点"、"今天该复习什么"

        Returns:
            JSON 格式的学习状态，包含 weak_points 和 reviews 字段。
        """
        try:
            # 分类查询意图
            query_type = classify_query(query)

            result = {
                "query_type": query_type,
                "weak_points": [],
                "reviews": [],
            }

            # 查询薄弱点
            if query_type in ["weakness", "status", "all"]:
                wps = await WeakPointManager().query_all(
                    conds=[WeakPointTable.scene_id == scene_id, WeakPointTable.deleted_at.is_(None)],
                    orders=[WeakPointTable.correct_rate.asc()],
                    limit=5,
                )
                result["weak_points"] = [
                    {
                        "concept": wp.concept,
                        "correct_rate": wp.correct_rate,
                        "mastery_level": wp.mastery_level,
                        "next_review": wp.next_review_at.strftime("%Y-%m-%d") if wp.next_review_at else None,
                    }
                    for wp in wps
                ]

            # 查询复习任务
            if query_type in ["review", "status", "all"]:
                tasks = await ReviewTaskManager().query_all(
                    conds=[
                        ReviewTaskTable.scene_id == scene_id,
                        ReviewTaskTable.status == "pending",
                        ReviewTaskTable.deleted_at.is_(None),
                    ],
                    orders=[ReviewTaskTable.due_at.asc()],
                    limit=5,
                )
                result["reviews"] = [
                    {
                        "concept": t.concept,
                        "due_at": t.due_at.strftime("%Y-%m-%d") if t.due_at else None,
                        "is_overdue": t.due_at < datetime.now() if t.due_at else False,
                    }
                    for t in tasks
                ]

            logger.info(f"[Tool:query_memory] query='{query}' type={query_type}")
            return json.dumps(result, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[Tool:query_memory] error: {e}")
            return json.dumps({"error": str(e), "weak_points": [], "reviews": []}, ensure_ascii=False)

    return query_memory


def build_agent_tools(scene_id: str, enabled_tools: list[str], eval_rubric: dict | None = None) -> list:
    """根据场景配置动态装配工具集。

    Args:
        scene_id: 场景 ID。
        enabled_tools: 启用的工具列表。
        eval_rubric: 评分规则配置。

    Returns:
        LangChain 工具列表。
    """
    all_tools = {
        "qa": lambda: make_search_knowledge_tool(scene_id),
        "quiz": lambda: make_generate_quiz_tool(scene_id),
        "update_weakness": lambda: make_update_weakness_tool(scene_id),
        "rubric_eval": lambda: make_rubric_eval_tool(eval_rubric or {}),
        "schedule": lambda: make_schedule_review_tool(scene_id),
        "crawler": lambda: make_web_search_tool(),
        "query_memory": lambda: make_query_memory_tool(scene_id),
    }

    selected = [all_tools[name]() for name in enabled_tools if name in all_tools]

    if not any(t.name == "search_knowledge" for t in selected):
        selected.insert(0, make_search_knowledge_tool(scene_id))

    logger.info(f"[AgentTools] Built {len(selected)} tools for scene={scene_id}")
    return selected


def build_tools_for_scene(user_id: str, scene_id: str, tools_enabled: list[str]) -> list:
    """根据场景配置动态装配工具集。

    Args:
        user_id: 用户 ID（保留参数）。
        scene_id: 场景 ID。
        tools_enabled: 启用的工具列表。

    Returns:
        LangChain 工具列表。
    """
    return build_agent_tools(scene_id=scene_id, enabled_tools=tools_enabled, eval_rubric={})
