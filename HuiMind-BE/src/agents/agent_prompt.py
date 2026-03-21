import json


PERSONA_SKILLS = {
    "严师型": "你的风格严格、直接、重结果，但仍然关心用户成长。",
    "鼓励型": "你的风格积极、鼓励、耐心，善于缓解焦虑并给予信心。",
    "陪伴型": "你的风格温和、稳定、细致，像长期陪学的伙伴。",
}


BASE_AGENT_RULES = """你是 AI 伴学平台的学习助手「HuiMind Buddy」。

平台级原则：
1. 优先结合用户上传资料、历史上下文和当前场景回答。
2. 使用用户资料内容时，必须标注来源，如 [来源：文件名]。
3. 如果资料中没有直接依据，要明确说明，并提供通用方法指导；不得伪造引用。
4. 回答应清晰、可执行、贴合用户当前目标。
"""


def build_system_prompt(*, scene, persona: str) -> str:
    persona_prompt = PERSONA_SKILLS.get(persona, PERSONA_SKILLS["陪伴型"])
    scene_name = scene.name if scene else "通用学习"
    scene_prompt = scene.system_prompt if scene else ""
    skill_prompt = scene.skill_prompt if scene else ""
    rubric = scene.eval_rubric if scene else {}

    policy = "\n".join(
        [
            "## 回答策略",
            "- 除非用户明确要求纯规划/闲聊，否则先检索知识库再回答。",
            "- 使用知识库内容时必须标注来源。",
            "- 如果知识库没有直接内容，可以提供通用方法指导，但要明确说明不是来自用户资料。",
            "- 结论先行，给出可执行的下一步。",
        ]
    )
    rubric_block = f"## 评分标准\n{json.dumps(rubric, ensure_ascii=False)}" if rubric else ""
    blocks = [
        BASE_AGENT_RULES.strip(),
        f"## 表达人格\n{persona_prompt}".strip(),
        f"## 当前场景\n场景名称：{scene_name}\n\n{scene_prompt}".strip(),
        f"## 场景技能\n{skill_prompt}".strip(),
        policy.strip(),
        rubric_block.strip(),
    ]
    return "\n\n---\n\n".join([b for b in blocks if b])
