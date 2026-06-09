"""学生画像智能体 — 逐维度提问，DeepSeek对话+千问生成画像"""

import json
from app.services.llm import chat_deepseek, chat_qwen

# 7个维度，按提问顺序排列
DIMENSIONS_ORDER = [
    ("knowledge_base", "知识基础", "学过哪些课程、掌握哪些技能、当前水平如何"),
    ("learning_style", "学习风格", "喜欢怎么学：看视频/读文档/动手做/听讲解"),
    ("weak_points", "学习难点", "哪些知识点觉得困难、哪些方面需要加强"),
    ("interests", "兴趣方向", "对什么主题或领域最感兴趣"),
    ("goals", "学习目标", "为什么学、想达到什么水平、职业规划"),
    ("learning_pace", "学习节奏", "每天能投入多少时间、什么时段效率最高"),
    ("interaction_pref", "交互偏好", "喜欢简洁直接还是详细展开、图文还是纯文字"),
]

PROFILE_DIMENSIONS = {k: f"{label}：{desc}" for k, label, desc in DIMENSIONS_ORDER}

# ========== DeepSeek 负责：对话提问 + 提取回答 ==========

QUESTION_PROMPT = """你是一个学习顾问，正在逐步了解学生。

{asked_summary}

学生刚才回答了关于「{prev_label}」的问题：{prev_answer}

你必须做到以下几点：
1. 先用1句话简单回应学生刚才说的内容，表示你在认真听（比如"了解了，你在这方面有一定基础"或"听起来你对这块很有热情"）
2. 然后自然过渡到下一个话题：{dim_label}（{dim_desc}）
3. 最后用友好的语气提出一个关于这个新维度的问题

整个回复控制在2-4句话，像真正的对话一样，不要生硬跳转话题。

现在学生回答的上一个问题已经记录好了，你需要问的是关于「{dim_label}」的问题。"""

EXTRACT_PROMPT = """根据学生的回答，提取「{dim_label}」维度的画像描述。

对话上下文：{context}
学生最新回答：{answer}

请用一句话总结学生在「{dim_label}」这个维度上的特征，返回JSON：
{{"{dim_key}": "一句话特征描述"}}"""


def get_next_dimension(filled_dimensions: set) -> dict | None:
    """找到下一个未提问的维度"""
    for key, label, desc in DIMENSIONS_ORDER:
        if key not in filled_dimensions:
            return {"key": key, "label": label, "desc": desc}
    return None


def ask_dimension_question(dim_key: str, dim_label: str, dim_desc: str,
                           conversation: list, profile: dict,
                           prev_label: str = "", prev_answer: str = "") -> str:
    """AI回应学生回答 + 自然过渡到下一个维度"""
    asked_parts = []
    for k, label, _ in DIMENSIONS_ORDER:
        if k in profile and profile[k]:
            asked_parts.append(f"已了解{label}：{profile[k]}")
    asked_summary = "\n".join(asked_parts) if asked_parts else "尚未收集任何信息"

    # 第一条消息：简单打招呼 + 提问，不需要"回应"
    if not prev_answer:
        resp = chat_deepseek([{
            "role": "system",
            "content": f"""你是一个友好的学习顾问，正在了解一位新学生。

{asked_summary}

请用自然友好的语气打个招呼，然后问一个关于「{dim_label}」的问题（{dim_desc}）。
2-3句话，像真人对话一样，不要模板化。"""
        }], temperature=0.8, max_tokens=200)
        return resp.choices[0].message.content.strip()

    # 后续消息：先回应，再过渡
    if not prev_label:
        prev_label = "上一个维度"

    resp = chat_deepseek([{
        "role": "system",
        "content": QUESTION_PROMPT.format(
            dim_label=dim_label, dim_desc=dim_desc,
            asked_summary=asked_summary,
            prev_label=prev_label, prev_answer=prev_answer,
        )
    }], temperature=0.8, max_tokens=400)

    return resp.choices[0].message.content.strip()


def extract_dimension_answer(dim_key: str, dim_label: str,
                             conversation: list, user_answer: str) -> str | None:
    """从学生的回答中提取该维度的特征描述"""
    # 取最近几轮对话作为上下文
    context = "\n".join(
        f"{'学生' if m['role'] == 'user' else 'AI'}：{m['content']}"
        for m in conversation[-6:]
    )

    resp = chat_deepseek([{
        "role": "system",
        "content": EXTRACT_PROMPT.format(
            dim_label=dim_label,
            dim_key=dim_key,
            context=context,
            answer=user_answer,
        )
    }], temperature=0.3, max_tokens=200, json_mode=True)

    try:
        text = resp.choices[0].message.content.strip()
        # 清理可能的 markdown 代码块
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("\n", 1)[0]
        data = json.loads(text)
        extracted = data.get(dim_key, "").strip()
        if extracted:
            return extracted
    except (json.JSONDecodeError, KeyError):
        pass

    # 兜底：如果 LLM 提取失败，直接用用户原话（确保维度不会卡住）
    if user_answer and len(user_answer) > 2:
        return f"学生提到：{user_answer[:100]}"
    return None


# ========== DeepSeek 生成文本报告 + 千问设计视觉 ==========

import re as _re

def generate_final_profile(profile: dict, conversation: list) -> dict:
    """一次LLM调用同时生成文字报告 + ECharts雷达图配置（参考DeepDiagram的一次输出模式）"""
    conv_text = "\n".join(
        f"{'学生' if m['role'] == 'user' else 'AI'}：{m['content']}"
        for m in conversation
    )

    profile_lines = []
    for k, label, _ in DIMENSIONS_ORDER:
        val = profile.get(k, "")
        profile_lines.append(f"- {label}：{val}" if val else f"- {label}：待了解")
    profile_text = "\n".join(profile_lines)

    # 一次调用：文字报告 + 评分 + 视觉元数据 + ECharts配置
    resp = chat_deepseek([{
        "role": "system",
        "content": f"""你是学习画像分析师+视觉设计师。请根据学生数据一次性生成完整画像报告。

学生数据：
{profile_text}

对话记录：
{conv_text}

请严格按照以下格式输出（用 ===SECTION=== 分隔）：

===REPORT===
（纯文本报告，不要JSON，不要代码块）

### 🌟 学习画像总览
2-3句话概括学习特质，用第二人称

### 🔍 多维分析
每个维度1-2句分析

### 📌 个性化学习建议
3条具体可执行建议

### 🎯 推荐学习资源
3种适合的资源形式

===SCORES===
（纯JSON对象，7个维度1-10分）
{{"知识基础": 8, "学习风格": 7, "学习难点": 5, "兴趣方向": 9, "学习目标": 8, "学习节奏": 7, "交互偏好": 6}}

===VISUAL===
（纯JSON对象，用于前端可视化）
{{
    "card_title": "一句话标签（如：夜读型AI探索者）",
    "atmosphere": "视觉氛围一句话",
    "strengths": ["优势1", "优势2"],
    "growth_areas": ["成长方向1", "成长方向2"],
    "learning_quote": "适合的学习格言"
}}

===RADAR===
（纯JSON对象，7维度0-1的值，用于ECharts雷达图）
{{
    "indicator": [{{"name": "知识基础", "max": 1}}, ...共7个],
    "value": [0.8, 0.7, 0.3, 0.9, 0.8, 0.7, 0.6]
}}

===RESOURCES===
（纯JSON数组，推荐5个具体学习资源）
[
    {{"title": "资源名称", "type": "课程/书籍/视频/工具/社区", "url": "搜索关键词或链接", "why": "1句话推荐理由", "difficulty": "入门/中级/高级"}}
]

===ROADMAP===
（纯JSON数组，3-5步学习路线）
[
    {{"step": 1, "title": "阶段名称", "duration": "建议时长", "focus": "本阶段重点", "milestone": "阶段成果"}}
]

===TAGS===
（纯JSON数组，5-8个标签词概括这个学习者）
["标签1", "标签2", "标签3", ...]

只按格式输出，不要额外解释。"""
    }], temperature=0.6, max_tokens=2000)

    full_text = resp.choices[0].message.content.strip()

    # 解析各SECTION
    def _extract_section(text: str, tag: str) -> str:
        m = _re.search(rf'==={tag}===\s*\n?(.*?)(?=\n===|\Z)', text, _re.DOTALL)
        return m.group(1).strip() if m else ""

    report = _extract_section(full_text, "REPORT")
    report = _re.sub(r'```[^`]*```', '', report)  # 清理可能的代码块
    report = _re.sub(r'\n\s*\n\s*\n', '\n\n', report).strip()

    # 处理评分
    scores = {}
    scores_text = _extract_section(full_text, "SCORES")
    try:
        scores = json.loads(scores_text)
    except Exception:
        for k, label, _ in DIMENSIONS_ORDER:
            val = profile.get(k, "")
            scores[label] = min(9, max(3, len(val) // 12 + 4)) if val else 3

    # 处理视觉
    visual = {
        "radar_scores": scores,
        "card_title": "", "atmosphere": "",
        "strengths": [], "growth_areas": [], "learning_quote": "",
    }
    visual_text = _extract_section(full_text, "VISUAL")
    try:
        visual.update(json.loads(visual_text))
    except Exception:
        sorted_dims = sorted(
            [(label, int(scores.get(label, 5))) for _, label, _ in DIMENSIONS_ORDER],
            key=lambda x: x[1], reverse=True
        )
        visual["card_title"] = f"{sorted_dims[0][0]}型学习者"
        visual["strengths"] = [f"{sorted_dims[0][0]}突出", f"{sorted_dims[1][0]}良好"]
        visual["growth_areas"] = [f"{sorted_dims[-1][0]}可加强"]

    # 处理雷达图数据
    radar = {"indicator": [], "value": []}
    radar_text = _extract_section(full_text, "RADAR")
    try:
        radar = json.loads(radar_text)
    except Exception:
        # 用 scores 兜底
        for _, label, _ in DIMENSIONS_ORDER:
            radar["indicator"].append({"name": label, "max": 1})
            radar["value"].append(scores.get(label, 5) / 10)
    visual["radar_data"] = radar

    # 学习资源
    resources_text = _extract_section(full_text, "RESOURCES")
    try:
        visual["resources"] = json.loads(resources_text)
    except Exception:
        visual["resources"] = []

    # 学习路线
    roadmap_text = _extract_section(full_text, "ROADMAP")
    try:
        visual["roadmap"] = json.loads(roadmap_text)
    except Exception:
        visual["roadmap"] = []

    # 标签
    tags_text = _extract_section(full_text, "TAGS")
    try:
        visual["tags"] = json.loads(tags_text)
    except Exception:
        visual["tags"] = []

    return {"report": report, "visual": visual, "profile": profile}
