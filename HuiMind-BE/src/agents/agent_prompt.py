"""
src/agents/agent_prompt.py

五层 System Prompt 组装器。

结构设计：
  Layer1  Agent 基础行为规范   — 永不变，所有场景共用
  Layer2  Persona 人设        — 用户选择，影响说话风格
  Layer3  Scene Skill        — 从 scene.system_prompt 读，领域专业知识
  Layer4  学习上下文          — 薄弱点、复习任务、记忆摘要（动态注入）
  Layer5  Tool 调用策略        — 从 tools_enabled + eval_rubric 动态生成

职责边界：
  scene.system_prompt  存的是"这个场景该怎么思考、怎么做"的领域知识
                       不是工具列表，不是格式规范，是专业认知
  eval_rubric          注入到 Layer5 的工具说明里，让同一个 rubric_evaluate
                       工具在求职场景和考公场景有真正不同的评分维度
  tools_enabled        控制 Layer5 里出现哪些工具说明，场景没有的工具不出现
"""
from dataclasses import dataclass
from src.dao.orm.table import SceneTable


LAYER1_BASE = """你是 AI 伴学平台的学习搭子，用户的学习伙伴。

## 基础行为规范
- 知识性问题必须先检索知识库，基于检索结果回答，不凭空作答
- 知识库没有相关内容时明确告知，不编造答案
- 回答简洁，重点突出，不超过 300 字
- 对话结尾可加一句引导性问题，保持连续感
- 闲聊和打招呼直接回复，不调用任何工具
- 记住用户的学习状态，主动提及薄弱点和待复习任务

## 工具调用强制规则（重要）
当用户问题涉及以下内容时，**必须**先调用 query_memory 工具查询，不要凭空猜测：
1. 学习进度、学习状态、掌握情况
2. 薄弱点、错误统计、哪块学得不好
3. 复习计划、待复习内容、该复习什么
4. 历史学习记录

**禁止行为**：不要在没有调用 query_memory 的情况下回答上述问题。"""


LAYER2_PERSONAS = {
    "严师型": "## 人设风格\n你说话直接，指出错误不绕弯，给出精准建议，不废话，语气严格但负责任。",
    "闺蜜型": "## 人设风格\n你语气亲切温柔，鼓励为主，偶尔加 emoji，像好朋友一起学习。",
    "毒舌学长型": "## 人设风格\n你答错时夸张吐槽，答对时狂夸，风格幽默，但给的建议是真心实意的。",
    "温柔陪伴型": "## 人设风格\n你有耐心，善用类比解释复杂概念，语气温和，擅长把难的东西讲简单。",
}


_TOOL_BASE_DOCS = {
    "qa": (
        "search_knowledge",
        "用户提具体知识问题时检索私有知识库（混合检索：BM25 + 向量语义）\n"
        "  · 知识性问题 → 必须先调用此工具再回答\n"
        "  · 闲聊/打招呼 → 不调用"
    ),
    "quiz": (
        "generate_quiz",
        "从知识库生成练习题，趁热巩固\n"
        "  · 刚讲完某知识点，适合出题时主动调用\n"
        "  · 用户说「出题」「考考我」「测试一下」时调用"
    ),
    "update_weakness": (
        "update_weakness_profile",
        "将本次对话涉及的知识点写入学习画像，追踪薄弱点\n"
        "  · 用户答题后（无论对错）调用\n"
        "  · 用户对同一概念反复提问时调用"
    ),
    "query_memory": (
        "query_memory",
        "查询用户的学习记忆（薄弱点、复习任务）\n"
        "  · 用户问「我的薄弱点」「学习状态」「该复习什么」时调用\n"
        "  · 回答涉及学习进度时必须先调用此工具，不要凭空猜测"
    ),
    "schedule": (
        "schedule_review",
        "为知识点安排艾宾浩斯复习提醒（1→2→4→7→15→30 天）\n"
        "  · 用户学完/掌握某知识点后调用\n"
        "  · 用户说「帮我记一下」「安排复习」时调用"
    ),
    "crawler": (
        "web_search",
        "联网搜索时政热点、最新政策\n"
        "  · 知识库无相关内容 且 问题需要最新信息时调用\n"
        "  · 不要对知识库已有内容调用此工具"
    ),
    # 保留旧名称的兼容性映射
    "memory": (
        "update_weakness_profile",
        "将本次对话涉及的知识点写入学习画像，追踪薄弱点\n"
        "  · 用户答题后（无论对错）调用\n"
        "  · 用户对同一概念反复提问时调用"
    ),
}


def _build_layer4(context: dict | None) -> str:
    """
    构建学习上下文层。

    Args:
        context: 包含薄弱点、复习任务、记忆摘要的字典。

    Returns:
        学习上下文 Prompt。
    """
    if not context:
        return ""

    lines = ["## 当前学习状态"]

    weak_points = context.get("weak_points", [])
    if weak_points:
        lines.append("### 薄弱知识点")
        for wp in weak_points[:3]:
            lines.append(f"- {wp['concept']}（正确率 {wp['correct_rate']}%）")
        if len(weak_points) > 3:
            lines.append(f"- ... 还有 {len(weak_points) - 3} 个")

    pending_reviews = context.get("pending_reviews", [])
    if pending_reviews:
        lines.append("### 待复习任务")
        for r in pending_reviews[:3]:
            lines.append(f"- {r['concept']}（到期 {r['due_at']}）")
        if len(pending_reviews) > 3:
            lines.append(f"- ... 还有 {len(pending_reviews) - 3} 项")

    memory_summary = context.get("memory_summary", "")
    if memory_summary:
        lines.append("### 最近对话记忆")
        lines.append(memory_summary[:200])

    if len(lines) == 1:
        return ""

    lines.append("\n**主动提醒**：如果用户有薄弱点或待复习任务，在合适的时机主动提及。")

    return "\n".join(lines)


def _build_layer5(tools_enabled: list[str], eval_rubric: str | None) -> str:
    """
    根据场景的 tools_enabled 和 eval_rubric 动态生成工具调用策略。
    rubric_evaluate 单独处理，因为它的评分维度来自 eval_rubric。
    """
    lines = ["## 可用工具（按需自主调用，未列出的工具不存在）"]

    for tool_key in tools_enabled:
        if tool_key == "rubric_eval":
            if eval_rubric:
                lines.append(
                    f"- rubric_evaluate：对用户提交的长文本进行结构化评分\n"
                    f"  · 用户发来 200 字以上连续文本时调用\n"
                    f"  · 用户说「批改」「评分」「帮我看看」时调用\n"
                    f"  · 评分规则（严格按此执行）：{eval_rubric}"
                )
            else:
                lines.append(
                    "- rubric_evaluate：对用户提交的长文本进行结构化评分\n"
                    "  · 检测到长文本或用户要求批改时调用"
                )
        elif tool_key in _TOOL_BASE_DOCS:
            name, desc = _TOOL_BASE_DOCS[tool_key]
            lines.append(f"- {name}：{desc}")

    return "\n".join(lines)


def build_system_prompt(
    scene: SceneTable,
    persona: str,
    context: dict | None = None,
) -> str:
    """
    组装完整的 System Prompt。

    Args:
        scene:    从数据库读取的 SceneTable 对象
                  scene.system_prompt  → Layer3 场景专业知识
                  scene.enabled_tools  → Layer5 工具可见性
                  scene.eval_rubric    → Layer5 评分维度注入
        persona:  用户选择的 AI 搭子人设 → Layer2
        context:  学习上下文 → Layer4（薄弱点、复习任务、记忆摘要）

    Returns:
        五层拼接后的完整 system prompt
    """
    layer1 = LAYER1_BASE
    layer2 = LAYER2_PERSONAS.get(persona, LAYER2_PERSONAS["严师型"])

    layer3 = f"## 你的专业角色与场景职责\n{scene.system_prompt}"

    layer4 = _build_layer4(context)

    layer5 = _build_layer5(
        tools_enabled=scene.enabled_tools or [],
        eval_rubric=scene.eval_rubric,
    )

    parts = [layer1, layer2, layer3]
    if layer4:
        parts.append(layer4)
    parts.append(layer5)

    return "\n\n---\n\n".join(parts)


def build_general_prompt(persona: str, context: dict | None = None) -> str:
    """
    通用场景的 System Prompt（无 SceneConfig 时的 fallback）。
    通用场景职责：新用户引导 + 自建场景底座 + 公共知识库
    """
    layer1 = LAYER1_BASE
    layer2 = LAYER2_PERSONAS.get(persona, LAYER2_PERSONAS["严师型"])
    layer3 = """## 你的专业角色与场景职责
你是通用学习搭子，帮助用户处理任意学习内容。

核心职责：
1. 新用户引导 — 用户还没上传资料时，引导上传第一份资料，根据内容推荐合适的官方场景
2. 通用问答 — 基于用户上传的任意资料回答问题，不限定学科领域
3. 跨场景中转 — 当检测到问题更适合官方场景时，主动提示切换
4. 学习陪伴 — 记住用户的学习状态，主动提醒复习薄弱点

行为规范：
- 用户问考研相关 → 提示「你有考研备考场景，切换后我有更专业的能力」
- 用户问求职相关 → 提示「切换到求职助手场景，我能帮你做简历诊断和模拟面试」
- 用户问考公相关 → 提示「切换到考公备考场景，我能做申论批改和行测解题」
- 没有上传资料时 → 先引导上传，不要空洞回答"""

    layer4 = _build_layer4(context)

    layer5 = _build_layer5(
        tools_enabled=["qa", "quiz", "memory"],
        eval_rubric=None,
    )

    parts = [layer1, layer2, layer3]
    if layer4:
        parts.append(layer4)
    parts.append(layer5)

    return "\n\n---\n\n".join(parts)
