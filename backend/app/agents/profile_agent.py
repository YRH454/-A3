"""学生画像智能体 — 基于 LangGraph 的对话式画像构建

借鉴 Agent4Edu 的 3 模块架构：认知画像 + 行为风格 + 动态记忆
对话流程：问候→基础信息→深层挖掘→画像确认→持续更新
"""
import json
from dataclasses import dataclass, field
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from app.services.llm import chat_qwen

# ---- 画像维度定义 ----
PROFILE_DIMENSIONS = {
    "knowledge_base": "知识基础：先修课程掌握程度、专业知识水平",
    "learning_style": "学习风格：视觉/听觉/读写/动手型(VARK)偏好",
    "cognitive_ability": "认知能力：逻辑推理、问题解决、记忆能力",
    "weak_points": "易错点偏好：高频错误知识点、薄弱环节",
    "interests": "兴趣方向：偏好的学习主题和内容类型",
    "learning_pace": "学习节奏：学习速度、专注时长、最佳学习时段",
    "goals": "目标导向：短期/长期学习目标、职业规划",
    "interaction_pref": "交互偏好：简洁/详细、文字/语音，对话风格偏好",
}

CONVERSATION_STAGES = [
    "greeting",           # 自我介绍，说明目的
    "basic_info",         # 收集专业、年级等基础信息
    "learning_style",     # 了解学习风格偏好
    "knowledge_check",    # 了解知识基础和薄弱点
    "goals_interests",    # 了解学习目标和兴趣
    "profile_confirm",    # 展示画像摘要，请求确认
    "done",               # 画像完成，可开始学习
]

# ---- State Definition ----
class ProfileState(TypedDict):
    messages: list          # 对话历史 [{role, content}]
    stage: str              # 当前对话阶段
    profile: dict           # 已抽取的画像数据
    collected_dimensions: list  # 已收集的维度
    user_id: int | None     # 用户ID

# ---- LLM Prompts ----
SYSTEM_PROMPT = """你是一个友好的学习顾问，正在帮助学生构建个人学习画像。你的任务是：

1. 通过自然对话了解学生的学习情况（不要像填表，要像聊天）
2. 逐步收集以下维度的信息：{dimensions}
3. 当前需要收集的维度：{current_dimension}
4. 已了解的信息：{collected_info}

对话规则：
- 每次只关注1-2个维度，不要一次问太多
- 用开放式问题引导，不要连珠炮式提问
- 根据学生的回答自然地追问细节
- 如果学生不清楚某方面，可以给出选项或示例帮助他们思考
- 对话风格温暖专业，像一位耐心的导师
- 回答要简短，一般不超过3句话

当前阶段：{stage_description}
如果当前阶段完成了，回复末尾加上 [NEXT_STAGE]"""

EXTRACT_PROFILE_PROMPT = """根据以下对话，提取学生的学习画像信息，返回JSON格式。

对话内容：
{conversation}

已抽取的画像：{existing_profile}

请从中提取新的或更新的画像信息，只返回JSON（不要markdown标记）：
{{
  "knowledge_base": "学生对先修课程的掌握情况（如：已学过Python基础，对机器学习有初步了解）",
  "learning_style": "学习风格偏好（如：visual/auditory/read-write/kinesthetic）",
  "cognitive_ability": "认知特点（如：逻辑推理较强，但记忆细节需要加强）",
  "weak_points": "薄弱知识点（如：数学推导、动态规划）",
  "interests": "兴趣方向（如：对NLP和计算机视觉感兴趣）",
  "learning_pace": "学习节奏偏好（如：喜欢集中长时间学习，每次2-3小时）",
  "goals": "学习目标（如：短期通过考试，长期成为AI工程师）",
  "interaction_pref": "交互偏好（如：喜欢详细解释，配合图示）"
}}

只返回有新信息的字段，没有新信息的字段返回空字符串。"""

# ---- Stage Descriptions ----
STAGE_DESCRIPTIONS = {
    "greeting": "向学生打招呼，简短介绍画像构建的目的（帮助他们获得个性化学习体验），然后自然过渡到了解基本信息",
    "basic_info": "了解学生的专业、年级、当前在学什么课程或技能",
    "learning_style": "了解学生喜欢怎么学习——看视频？读文档？做练习？喜欢自学还是跟课程？",
    "knowledge_check": "了解学生对相关领域的熟悉程度，哪里觉得难，哪里觉得有意思",
    "goals_interests": "了解学生的学习目标和兴趣：为什么学这门课？近期和长期目标是什么？",
    "profile_confirm": "向学生展示已构建的画像摘要，请他们确认或修正。确认后告知画像已经就绪，可以开始个性化学习了",
    "done": "画像已确认完成",
}

# ---- Agent Nodes ----

def greeting_node(state: ProfileState) -> ProfileState:
    """开场白 + 自然过渡到基础信息收集"""
    stage = "greeting"
    resp = chat_qwen([{
        "role": "system", "content": SYSTEM_PROMPT.format(
            dimensions=", ".join(PROFILE_DIMENSIONS.keys()),
            current_dimension="建立初步联系，了解基本背景",
            collected_info="尚未收集任何信息",
            stage_description=STAGE_DESCRIPTIONS[stage],
        )
    }, *state["messages"]], temperature=0.8, max_tokens=512)

    reply = resp.choices[0].message.content
    state["messages"].append({"role": "assistant", "content": reply})
    state["stage"] = "basic_info" if "[NEXT_STAGE]" in reply else stage
    return state


def basic_info_node(state: ProfileState) -> ProfileState:
    """收集专业、年级等基础信息"""
    existing = json.dumps(state.get("profile", {}), ensure_ascii=False)
    resp = chat_qwen([{
        "role": "system", "content": SYSTEM_PROMPT.format(
            dimensions=", ".join(PROFILE_DIMENSIONS.keys()),
            current_dimension="专业、年级、当前学习内容",
            collected_info=existing or "尚无",
            stage_description=STAGE_DESCRIPTIONS["basic_info"],
        )
    }, *state["messages"]], temperature=0.8, max_tokens=512)

    reply = resp.choices[0].message.content
    state["messages"].append({"role": "assistant", "content": reply})

    # Auto-advance logic
    if "[NEXT_STAGE]" in reply:
        state["stage"] = "learning_style"
        # Extract profile incrementally
        state["profile"] = _extract_profile(state["messages"], state.get("profile", {}))
    return state


def learning_style_node(state: ProfileState) -> ProfileState:
    """了解学习风格偏好"""
    existing = json.dumps(state.get("profile", {}), ensure_ascii=False)
    resp = chat_qwen([{
        "role": "system", "content": SYSTEM_PROMPT.format(
            dimensions=", ".join(PROFILE_DIMENSIONS.keys()),
            current_dimension="学习风格偏好（VARK）、喜欢的学习方式",
            collected_info=existing or "尚无",
            stage_description=STAGE_DESCRIPTIONS["learning_style"],
        )
    }, *state["messages"]], temperature=0.8, max_tokens=512)

    reply = resp.choices[0].message.content
    state["messages"].append({"role": "assistant", "content": reply})

    if "[NEXT_STAGE]" in reply:
        state["stage"] = "knowledge_check"
        state["profile"] = _extract_profile(state["messages"], state.get("profile", {}))
    return state


def knowledge_check_node(state: ProfileState) -> ProfileState:
    """了解知识基础和薄弱点"""
    existing = json.dumps(state.get("profile", {}), ensure_ascii=False)
    resp = chat_qwen([{
        "role": "system", "content": SYSTEM_PROMPT.format(
            dimensions=", ".join(PROFILE_DIMENSIONS.keys()),
            current_dimension="知识基础、学习难点、薄弱环节",
            collected_info=existing or "尚无",
            stage_description=STAGE_DESCRIPTIONS["knowledge_check"],
        )
    }, *state["messages"]], temperature=0.8, max_tokens=512)

    reply = resp.choices[0].message.content
    state["messages"].append({"role": "assistant", "content": reply})

    if "[NEXT_STAGE]" in reply:
        state["stage"] = "goals_interests"
        state["profile"] = _extract_profile(state["messages"], state.get("profile", {}))
    return state


def goals_interests_node(state: ProfileState) -> ProfileState:
    """了解学习目标和兴趣"""
    existing = json.dumps(state.get("profile", {}), ensure_ascii=False)
    resp = chat_qwen([{
        "role": "system", "content": SYSTEM_PROMPT.format(
            dimensions=", ".join(PROFILE_DIMENSIONS.keys()),
            current_dimension="学习目标、职业规划、兴趣方向",
            collected_info=existing or "尚无",
            stage_description=STAGE_DESCRIPTIONS["goals_interests"],
        )
    }, *state["messages"]], temperature=0.8, max_tokens=512)

    reply = resp.choices[0].message.content
    state["messages"].append({"role": "assistant", "content": reply})

    if "[NEXT_STAGE]" in reply:
        state["profile"] = _extract_profile(state["messages"], state.get("profile", {}))
        state["stage"] = "profile_confirm"
    return state


def profile_confirm_node(state: ProfileState) -> ProfileState:
    """展示画像摘要并请求确认"""
    profile = state.get("profile", {})
    summary = _format_profile_summary(profile)

    confirm_msg = {
        "role": "system",
        "content": f"""请用友好的语气向学生展示以下学习画像摘要，邀请他们确认或修正：

{summary}

规则：
- 先对学生的回答表示感谢
- 逐维度简要展示画像内容
- 询问"这些描述准确吗？有没有需要调整的地方？"
- 如果学生确认或提出修正，回复末尾加上 [DONE]"""
    }
    resp = chat_qwen([confirm_msg, *state["messages"]], temperature=0.7, max_tokens=512)

    reply = resp.choices[0].message.content
    state["messages"].append({"role": "assistant", "content": reply})

    if "[DONE]" in reply:
        state["stage"] = "done"
    elif "[NEXT_STAGE]" in reply:
        state["profile"] = _extract_profile(state["messages"], state.get("profile", {}))
    return state


def done_node(state: ProfileState) -> ProfileState:
    """画像完成"""
    state["stage"] = "done"
    state["profile"] = _extract_profile(state["messages"], state.get("profile", {}))
    complete_msg = {
        "role": "assistant",
        "content": "画像构建完成！现在开始，我将根据你的学习特点为你定制个性化的学习资源和计划。你可以随时让我帮你生成学习资料、规划学习路径，或者解答问题。准备好了吗？"
    }
    # Avoid duplicate
    if not state["messages"] or state["messages"][-1].get("content") != complete_msg["content"]:
        state["messages"].append(complete_msg)
    return state


# ---- Helper Functions ----

def _extract_profile(messages: list, existing: dict) -> dict:
    """从对话中抽取画像信息"""
    conversation = "\n".join(
        f"{'学生' if m['role']=='user' else '顾问'}：{m['content']}"
        for m in messages[-12:]  # 只看最近12轮
    )
    resp = chat_qwen([{
        "role": "system",
        "content": EXTRACT_PROFILE_PROMPT.format(
            conversation=conversation,
            existing_profile=json.dumps(existing, ensure_ascii=False)
        )
    }], temperature=0.3, max_tokens=1024, json_mode=True)

    try:
        new_data = json.loads(resp.choices[0].message.content)
        # Merge: new non-empty values override existing
        merged = {**existing}
        for k, v in new_data.items():
            if v and v.strip() and k in PROFILE_DIMENSIONS:
                merged[k] = v.strip()
        return merged
    except (json.JSONDecodeError, Exception):
        return existing


def _count_filled_dimensions(profile: dict) -> int:
    return sum(1 for v in profile.values() if v and v.strip())


def _format_profile_summary(profile: dict) -> str:
    """格式化画像为可读摘要"""
    lines = []
    for key, desc in PROFILE_DIMENSIONS.items():
        label = desc.split("：")[0]
        value = profile.get(key, "")
        icon = "✅" if value and value.strip() else "⬜"
        text = value if value else "待了解"
        lines.append(f"{icon} {label}：{text}")
    return "\n".join(lines)


# ---- Build Graph ----

def build_profile_graph() -> StateGraph:
    """构建画像对话图的编译版本"""
    builder = StateGraph(ProfileState)

    builder.add_node("greeting", greeting_node)
    builder.add_node("basic_info", basic_info_node)
    builder.add_node("learning_style", learning_style_node)
    builder.add_node("knowledge_check", knowledge_check_node)
    builder.add_node("goals_interests", goals_interests_node)
    builder.add_node("profile_confirm", profile_confirm_node)
    builder.add_node("done", done_node)

    # Route from start
    builder.add_edge(START, "greeting")

    # Stage routing: check current stage and route accordingly
    def route_by_stage(state: ProfileState) -> str:
        stage = state.get("stage", "greeting")
        if stage == "greeting":
            return "basic_info"
        elif stage == "learning_style":
            return "learning_style"
        elif stage == "knowledge_check":
            return "knowledge_check"
        elif stage == "goals_interests":
            return "goals_interests"
        elif stage == "profile_confirm":
            return "profile_confirm"
        elif stage == "done":
            return "done"
        return END

    builder.add_conditional_edges("greeting", route_by_stage)
    builder.add_conditional_edges("basic_info", route_by_stage)
    builder.add_conditional_edges("learning_style", route_by_stage)
    builder.add_conditional_edges("knowledge_check", route_by_stage)
    builder.add_conditional_edges("goals_interests", route_by_stage)
    builder.add_conditional_edges("profile_confirm", route_by_stage)
    builder.add_edge("done", END)

    return builder


profile_graph = build_profile_graph().compile()
