"""学生画像智能体 — AI主动提问，一问一答，对话结束后自动生成画像"""
import json
from app.services.llm import chat_deepseek, chat_qwen

PROFILE_DIMENSIONS = {
    "knowledge_base": "知识基础：学过哪些课程、掌握哪些技能、当前水平",
    "learning_style": "学习风格：喜欢看视频/读文档/动手做/听讲解，哪种方式学得最好",
    "weak_points": "学习难点：哪些知识点觉得难、哪些方面需要加强",
    "interests": "兴趣方向：对什么主题或领域最感兴趣、想深入学什么",
    "goals": "学习目标：为什么学、想达到什么水平、职业方向",
    "learning_pace": "学习节奏：每天能投入多少时间、喜欢集中学还是分散学",
    "interaction_pref": "交互偏好：喜欢简洁直接还是详细讲解、文字还是语音",
}

QUESTION_SUGGESTIONS = {
    "knowledge_base": [
        "先了解一下你的基础 —— 你之前学过哪些课程或技能？哪些是你觉得掌握得比较好的？",
        "你目前在学什么专业或方向？之前接触过相关的内容吗？",
    ],
    "learning_style": [
        "你平时学习新东西的时候，更喜欢哪种方式？看视频讲解、读文档教程、还是直接动手做项目？",
        "有没有哪种学习方式让你觉得效率特别高？",
    ],
    "weak_points": [
        "在学习过程中，哪些类型的知识点让你觉得比较吃力？",
        "回顾一下，有没有哪些内容你反复学习还是觉得没掌握？",
    ],
    "interests": [
        "在课程范围内，你对哪个方向最感兴趣？有没有特别想深入了解的主题？",
        "除了课内的内容，你还对哪些相关的领域好奇？",
    ],
    "goals": [
        "你希望通过学习达成什么目标？比如通过考试、做出项目、或者为职业做准备？",
        "你对未来的职业方向有什么想法？希望成为什么样的人？",
    ],
    "learning_pace": [
        "你平时大概每天能花多少时间学习？喜欢一口气学很久还是短时间多次？",
        "你在什么时间段学习状态最好？",
    ],
    "interaction_pref": [
        "在跟我交流的时候，你希望我怎么回答你？简洁直接一点还是详细展开？",
    ],
}

ASK_PROMPT = """你是一个专业的学习顾问，正在通过一问一答的方式了解学生，为其构建学习画像。

你需要从以下维度中选择一个尚未充分了解的维度，提出一个自然、友好的问题：
{dimensions_status}

对话规则：
- 每次只问一个问题，不要一次问多个
- 问题要自然，像聊天一样，不要像问卷调查
- 根据学生之前的回答，选择最合适的下一个维度
- 如果一个维度已经了解清楚了，就不要重复问
- 刚开始时优先了解基础信息（知识基础、学习目标）
- 问题要简短，一般不超过2句话
- 如果你觉得已经了解了足够多的信息（至少覆盖4-5个维度），在回复最后加上 [READY]

当前对话：
{conversation}

请只输出你要问的下一个问题，不要添加任何其他内容。如果已经了解充分，请输出 [READY]。"""

GENERATE_PROMPT = """根据以下对话，生成学生的完整学习画像。

对话记录：
{conversation}

请以学习顾问的口吻，生成一份结构化的学习画像报告。要求：
1. 用第二人称"你"来写，语气温暖专业
2. 每个维度写1-2句话的描述
3. 只描述从对话中获取到的信息，没有获取到的维度标注"待了解"
4. 在报告末尾，用一句话总结学生的学习特质

画像维度：
- 知识基础
- 学习风格
- 学习难点
- 兴趣方向
- 学习目标
- 学习节奏
- 交互偏好

直接输出画像报告文本，不要用JSON。"""

EXTRACT_JSON_PROMPT = """根据以下对话记录和学习画像报告，提取结构化的画像JSON。

对话：
{conversation}

画像报告：
{report}

请返回JSON格式（不要markdown标记）：
{{
  "knowledge_base": "一句话描述",
  "learning_style": "一句话描述",
  "weak_points": "一句话描述",
  "interests": "一句话描述",
  "goals": "一句话描述",
  "learning_pace": "一句话描述",
  "interaction_pref": "一句话描述"
}}

只返回JSON。"""


def get_dimensions_status(profile: dict) -> str:
    """返回每个维度的收集状态"""
    lines = []
    for key, desc in PROFILE_DIMENSIONS.items():
        label = desc.split("：")[0]
        filled = "已了解" if profile.get(key, "").strip() else "待了解"
        lines.append(f"- {label}：{filled}")
    return "\n".join(lines)


def count_filled(profile: dict) -> int:
    return sum(1 for v in profile.values() if v and v.strip())


def get_first_question() -> str:
    """开局：AI主动打招呼并问第一个问题"""
    resp = chat_deepseek([{
        "role": "system",
        "content": """你是一个友善的学习顾问。学生刚刚进入系统，你需要：
1. 简短打招呼（1句话）
2. 自然地开始了解学生的学习情况，问第一个问题
问题可以从这些角度选一个：专业/年级背景、学习目标、当前的课程、为什么想学习。
总长度控制在2-3句话，语气温暖自然。""",
    }], temperature=0.8, max_tokens=200)
    return resp.choices[0].message.content.strip()


def ask_question(conversation: list, profile: dict) -> dict:
    """AI根据当前画像状态，选择下一个维度并生成一个问题"""
    conv_text = "\n".join(
        f"{'学生' if m['role'] == 'user' else '顾问'}：{m['content']}"
        for m in conversation[-20:]
    )
    dims_status = get_dimensions_status(profile)

    resp = chat_deepseek([{
        "role": "system",
        "content": ASK_PROMPT.format(
            dimensions_status=dims_status,
            conversation=conv_text,
        )
    }], temperature=0.8, max_tokens=256)

    reply = resp.choices[0].message.content.strip()

    # Check if AI thinks we have enough info
    if "[READY]" in reply:
        return {"ready": True, "question": None}

    return {"ready": False, "question": reply}


def extract_current_answer(conversation: list, profile: dict) -> dict:
    """从最新一轮对话中提取画像信息（增量更新）"""
    conv_text = "\n".join(
        f"{'学生' if m['role'] == 'user' else '顾问'}：{m['content']}"
        for m in conversation[-8:]
    )
    existing_str = json.dumps(profile, ensure_ascii=False) if profile else "尚未提取"

    resp = chat_deepseek([{
        "role": "system",
        "content": f"""分析以下最新对话，提取学生信息到学习画像。

已知画像：{existing_str}

维度说明：
- knowledge_base: 知识基础（学过什么、掌握水平）
- learning_style: 学习风格（视频/文档/动手/听觉）
- weak_points: 学习难点
- interests: 兴趣方向
- goals: 学习目标
- learning_pace: 学习节奏和时间投入
- interaction_pref: 交互偏好

请输出JSON，只包含从本段对话中新获取到的维度（不要输出未提到的维度）：""",
    }, {
        "role": "user",
        "content": conv_text,
    }], temperature=0.3, max_tokens=512, json_mode=True)

    try:
        raw = resp.choices[0].message.content.strip()
        new_data = json.loads(raw)
        if not isinstance(new_data, dict):
            return profile
        merged = {**profile}
        for k, v in new_data.items():
            if v and str(v).strip() and k in PROFILE_DIMENSIONS:
                merged[k] = str(v).strip()
        return merged
    except Exception:
        return profile


def generate_profile(conversation: list) -> dict:
    """对话结束后，生成完整的画像报告和结构化数据"""
    conv_text = "\n".join(
        f"{'学生' if m['role'] == 'user' else '顾问'}：{m['content']}"
        for m in conversation
    )

    # Step 1: 生成可读的画像报告
    report_resp = chat_qwen([{
        "role": "system",
        "content": GENERATE_PROMPT.format(conversation=conv_text),
    }], temperature=0.7, max_tokens=1024)

    report = report_resp.choices[0].message.content.strip()

    # Step 2: 从报告中提取结构化JSON
    json_resp = chat_qwen([{
        "role": "system",
        "content": EXTRACT_JSON_PROMPT.format(conversation=conv_text, report=report),
    }], temperature=0.2, max_tokens=512, json_mode=True)

    try:
        profile_json = json.loads(json_resp.choices[0].message.content)
    except (json.JSONDecodeError, Exception):
        profile_json = {}

    return {
        "report": report,
        "profile": profile_json,
    }
