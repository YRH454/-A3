"""智能辅导 Agent — 多模式回答 + 画像关联 + 追问上下文"""

import json
import logging
from app.services.llm import chat_deepseek, chat_deepseek_stream, chat_qwen_stream
from app.services.profile_db import get_profile

logger = logging.getLogger(__name__)

# ==================== 4种回答模式 ====================

MODE_PROMPTS = {
    "text": """你是一位专业的AI辅导老师。请详细解答用户的学习问题。
要求：
- 用清晰的结构回答（标题、段落、列表）
- 包含必要的解释和具体例子
- 语言通俗易懂，避免堆砌术语
- 适当使用类比帮助理解
- Markdown格式输出""",

    "diagram": """你是一位擅长可视化的AI辅导老师。请解答问题并用结构化图解展示概念。
要求：
- 先用文字简要解释核心概念
- 然后用 Mermaid 图表（flowchart/mindmap/sequence）展示知识结构
- 如果Mermaid不适合，用ASCII图或结构化表格展示
- 图解要清晰、层次分明
- Markdown格式，Mermaid用 ```mermaid 代码块""",

    "video": """你是一位教学视频导演。请为用户的问题设计一个3-5分钟的教学视频脚本。
要求：
- 包含开场引入、核心讲解（分步骤）、总结回顾
- 每个段落标注时间轴（如 [00:00-00:30]）
- 描述画面内容（适合PPT或动画展示）
- 包含旁白文字
- 最后给出一段英文AI视频生成Prompt
- Markdown格式""",

    "code": """你是一位专业的编程老师。请为用户的问题提供完整的代码示例。
要求：
- 代码要完整可运行，包含必要的import
- 每个关键步骤都有中文注释
- 包含运行说明和预期输出
- 如果涉及多个文件，分别标注文件名
- 先简要解释思路，再给代码
- Markdown格式，代码用 ```language 代码块""",
}


# ==================== 画像上下文 ====================

def build_profile_context(user_id: int) -> str:
    """从DB读取用户画像，构建上下文字符串"""
    profile = get_profile(user_id)
    if not profile or not profile.get("profile"):
        return ""

    data = profile["profile"]
    if not isinstance(data, dict):
        return ""

    dim_map = {
        "knowledge_base": "知识基础",
        "learning_style": "学习风格",
        "weak_points": "学习难点",
        "interests": "兴趣方向",
        "goals": "学习目标",
        "learning_pace": "学习节奏",
        "interaction_pref": "交互偏好",
    }

    lines = []
    has_data = False
    for key, label in dim_map.items():
        val = data.get(key, "")
        if isinstance(val, str) and val.strip():
            lines.append(f"- {label}：{val}")
            has_data = True

    if not has_data:
        return ""

    return "\n\n【当前学生画像】\n" + "\n".join(lines) + "\n\n请根据以上画像调整回答风格和深度。"


# ==================== 追问相关性判断 ====================

def check_follow_up_relevance(new_question: str, prev_question: str, prev_answer: str) -> bool:
    """用轻量LLM调用判断新问题是否与上文相关"""
    try:
        resp = chat_deepseek([
            {"role": "system", "content": "判断用户的新问题是否与之前讨论的主题相关。仅回复\"相关\"或\"无关\"，不要解释。"},
            {"role": "user", "content": f"之前的问题：{prev_question}\n之前的回答主题：{prev_answer[:500]}\n\n新问题：{new_question}\n\n回复\"相关\"或\"无关\"。"}
        ], temperature=0.1, max_tokens=10)
        result = resp.choices[0].message.content.strip()
        return "相关" in result and "无关" not in result
    except Exception:
        return False


# ==================== 构建消息 ====================

def build_tutor_messages(
    question: str,
    mode: str = "text",
    user_id: int = 0,
    history: list = None,
    parent_qa: dict = None,
) -> list:
    """构建发送给LLM的消息列表"""
    # 基础 system prompt
    system_prompt = MODE_PROMPTS.get(mode, MODE_PROMPTS["text"])

    # 注入画像上下文
    profile_ctx = build_profile_context(user_id)
    if profile_ctx:
        system_prompt += profile_ctx

    # 构建 user 消息
    if parent_qa:
        # 追问模式：注入上下文
        user_content = f"之前的问答：\n问：{parent_qa['question']}\n答：{parent_qa['answer'][:2000]}\n\n用户的追问：{question}"
    else:
        user_content = question

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # 加入最近几轮对话历史（最多3轮）
    if history:
        recent = history[-6:]  # 最多3轮（每轮2条）
        for msg in recent:
            messages.append({"role": msg["role"], "content": msg["content"][:1000]})

    messages.append({"role": "user", "content": user_content})

    return messages


def stream_tutor_answer(messages: list):
    """流式生成辅导回答，返回chunk迭代器"""
    return chat_deepseek_stream(messages, temperature=0.5, max_tokens=4096)
