"""
src/agents/agent_prompt.py

四层 System Prompt 组装器。

结构设计：
  Layer1  Agent 基础行为规范   — 永不变，所有场景共用
  Layer2  Persona 人设        — 用户选择，影响说话风格
  Layer3  Scene Skill        — 从 scene.system_prompt 读，领域专业知识
  Layer4  Tool 调用策略        — 从 tools_enabled + eval_rubric 动态生成

职责边界：
  scene.system_prompt  存的是"这个场景该怎么思考、怎么做"的领域知识
                       不是工具列表，不是格式规范，是专业认知
  eval_rubric          注入到 Layer4 的工具说明里，让同一个 rubric_evaluate
                       工具在求职场景和考公场景有真正不同的评分维度
  tools_enabled        控制 Layer4 里出现哪些工具说明，场景没有的工具不出现
"""
from dataclasses import dataclass
from src.dao.orm.table import SceneTable


# ──────────────────────────────────────────────────────────────
# Layer 1: Agent 基础行为规范（所有场景共用，永不变）
# 只写"怎么做"的规范，不写"做什么"的领域知识
# ──────────────────────────────────────────────────────────────
LAYER1_BASE = """你是 AI 伴学平台的学习助手「Nova」。

## 基础行为规范
- 知识性问题必须先检索知识库，基于检索结果回答，不凭空作答
- 引用知识库内容时标注来源：[来源：文件名 第X段]
- 知识库没有相关内容时明确告知，不编造答案
- 回答简洁，重点突出，不超过 300 字
- 对话结尾可加一句引导性问题，保持连续感
- 闲聊和打招呼直接回复，不调用任何工具"""


# ──────────────────────────────────────────────────────────────
# Layer 2: Persona 人设（用户选择，只影响说话风格）
# ──────────────────────────────────────────────────────────────
LAYER2_PERSONAS = {
    "严师型": "## 人设风格\n你说话直接，指出错误不绕弯，给出精准建议，不废话，语气严格但负责任。",
    "闺蜜型": "## 人设风格\n你语气亲切温柔，鼓励为主，偶尔加 emoji，像好朋友一起学习。",
    "毒舌学长型": "## 人设风格\n你答错时夸张吐槽，答对时狂夸，风格幽默，但给的建议是真心实意的。",
    "温柔陪伴型": "## 人设风格\n你有耐心，善用类比解释复杂概念，语气温和，擅长把难的东西讲简单。",
}


# ──────────────────────────────────────────────────────────────
# Layer 4: Tool 调用策略（根据 tools_enabled + eval_rubric 动态生成）
# 场景没有的工具不出现，eval_rubric 直接注入工具说明
# ──────────────────────────────────────────────────────────────

# 每个 tool 的通用说明模板
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
    "memory": (
        "update_weakness_profile",
        "将本次对话涉及的知识点写入学习画像，追踪薄弱点\n"
        "  · 用户答题后（无论对错）调用\n"
        "  · 用户对同一概念反复提问时调用"
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
}


def _build_layer4(tools_enabled: list[str], eval_rubric: str | None) -> str:
    """
    根据场景的 tools_enabled 和 eval_rubric 动态生成工具调用策略。
    rubric_evaluate 单独处理，因为它的评分维度来自 eval_rubric。
    """
    lines = ["## 可用工具（按需自主调用，未列出的工具不存在）"]

    for tool_key in tools_enabled:
        if tool_key == "rubric_eval":
            # rubric_evaluate 的说明需要注入 eval_rubric 配置
            # 这是 eval_rubric 字段第一次真正被使用
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


# ──────────────────────────────────────────────────────────────
# 公共接口：四层组装
# ──────────────────────────────────────────────────────────────

def build_system_prompt(scene: SceneTable, persona: str) -> str:
    """
    组装完整的 System Prompt。

    Args:
        scene:    从数据库读取的 SceneTable 对象
                  scene.system_prompt  → Layer3 场景专业知识
                  scene.tools_enabled  → Layer4 工具可见性
                  scene.eval_rubric    → Layer4 评分维度注入
        persona:  用户选择的 AI 搭子人设 → Layer2

    Returns:
        四层拼接后的完整 system prompt
    """
    layer1 = LAYER1_BASE
    layer2 = LAYER2_PERSONAS.get(persona, LAYER2_PERSONAS["严师型"])

    # Layer3: 场景专业知识，直接从数据库读
    # 这里存的是"求职助手该怎么做简历诊断"，不是工具列表
    layer3 = f"## 你的专业角色与场景职责\n{scene.system_prompt}"

    # Layer4: 根据场景配置动态生成，eval_rubric 注入
    layer4 = _build_layer4(
        tools_enabled=scene.tools_enabled or [],
        eval_rubric=scene.eval_rubric,
    )

    return "\n\n---\n\n".join([layer1, layer2, layer3, layer4])


def build_general_prompt(persona: str) -> str:
    """
    通用场景的 System Prompt（无 SceneConfig 时的 fallback）。
    通用场景职责：新用户引导 + 自建场景底座 + 公共知识库
    """
    layer1 = LAYER1_BASE
    layer2 = LAYER2_PERSONAS.get(persona, LAYER2_PERSONAS["严师型"])
    layer3 = """## 你的专业角色与场景职责
你是通用学习助手，帮助用户处理任意学习内容。

核心职责：
1. 新用户引导 — 用户还没上传资料时，引导上传第一份资料，根据内容推荐合适的官方场景
2. 通用问答 — 基于用户上传的任意资料回答问题，不限定学科领域
3. 跨场景中转 — 当检测到问题更适合官方场景时，主动提示切换

行为规范：
- 用户问考研相关 → 提示「你有考研备考场景，切换后我有更专业的能力」
- 用户问求职相关 → 提示「切换到求职助手场景，我能帮你做简历诊断和模拟面试」
- 用户问考公相关 → 提示「切换到考公备考场景，我能做申论批改和行测解题」
- 没有上传资料时 → 先引导上传，不要空洞回答"""

    layer4 = _build_layer4(
        tools_enabled=["qa", "quiz", "memory"],
        eval_rubric=None,
    )

    return "\n\n---\n\n".join([layer1, layer2, layer3, layer4])
