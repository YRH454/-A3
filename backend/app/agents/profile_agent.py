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
        data = json.loads(resp.choices[0].message.content.strip())
        return data.get(dim_key, "").strip() or None
    except json.JSONDecodeError:
        return None


# ========== DeepSeek 生成文本报告 + 千问设计视觉 ==========

def generate_final_profile(profile: dict, conversation: list) -> dict:
    """DeepSeek生成文本总结，千问设计可视化方案"""
    conv_text = "\n".join(
        f"{'学生' if m['role'] == 'user' else 'AI'}：{m['content']}"
        for m in conversation
    )

    profile_lines = []
    for k, label, _ in DIMENSIONS_ORDER:
        val = profile.get(k, "")
        profile_lines.append(f"- {label}：{val}" if val else f"- {label}：待了解")
    profile_text = "\n".join(profile_lines)

    # Step 1: DeepSeek 快速生成纯文本报告（不要JSON）
    report_resp = chat_deepseek([{
        "role": "system",
        "content": f"""你是学习画像分析师。根据数据生成一份优雅的画像报告。

学生数据：
{profile_text}

对话记录：
{conv_text}

请按以下结构输出纯文本报告：

---

### ? 学习画像总览
2-3句话概括学习特质，用第二人称"你"

### ? 多维分析
每个维度1-2句分析

### ? 个性化学习建议
3条具体可执行的建议，编号列出

### ? 推荐学习资源类型
适合你的3种资源形式

---

要求：语气温暖专业，像一位了解你的导师。不要输出JSON、代码块或任何格式标记。"""
    }], temperature=0.6, max_tokens=1500)

    report = report_resp.choices[0].message.content.strip()
    # Strip any JSON/code blocks that DeepSeek might still sneak in
    import re
    report = re.sub(r'```json\s*\{[\s\S]*?\}\s*```', '', report)
    report = re.sub(r'```\s*\{[\s\S]*?\}\s*```', '', report)
    report = re.sub(r'\n\{[^{]*"radar_scores"[\s\S]*?\n\}', '', report)
    report = re.sub(r'\n\s*\n\s*\n', '\n\n', report)
    report = report.strip()

    # Step 2: DeepSeek 提取评分数据
    scores_resp = chat_deepseek([{
        "role": "system",
        "content": f"""根据画像数据，给7个维度打分(1-10)，返回纯JSON：

{profile_text}

格式：{{"知识基础": 8, "学习风格": 7, "学习难点": 5, "兴趣方向": 9, "学习目标": 8, "学习节奏": 7, "交互偏好": 6}}

只返回JSON对象，不要其他文字。"""
    }], temperature=0.2, max_tokens=200, json_mode=True)

    scores = {}
    try:
        scores = json.loads(scores_resp.choices[0].message.content.strip())
    except Exception:
        for k, label, _ in DIMENSIONS_ORDER:
            val = profile.get(k, "")
            scores[label] = min(9, max(3, len(val) // 12 + 4)) if val else 3

    # Step 3: 千问设计视觉方案（颜色、氛围、标签）
    visual_resp = chat_qwen([{
        "role": "system",
        "content": f"""你是视觉设计师。根据学生画像设计一个可视化方案。

画像数据：
{profile_text}

请设计：返回纯JSON（不要markdown标记）
{{
    "card_title": "一句话概括这个学生的标签（如：夜读型AI探索者）",
    "atmosphere": "视觉氛围描述（如：深夜星空下的思考者）",
    "color_gradient": ["#主色", "#辅色", "#点缀色"],
    "strengths": ["优势1", "优势2"],
    "growth_areas": ["成长方向1", "成长方向2"],
    "learning_quote": "一句适合这位学生的学习格言"
}}"""
    }], temperature=0.8, max_tokens=600, json_mode=True)

    visual = {
        "radar_scores": scores,
        "card_title": "",
        "atmosphere": "",
        "color_gradient": ["#D4845A", "#5B8C7B", "#DEB040"],
        "strengths": [],
        "growth_areas": [],
        "learning_quote": "",
    }
    try:
        vdata = json.loads(visual_resp.choices[0].message.content.strip())
        visual.update(vdata)
    except Exception:
        # Fallback: use data-driven defaults
        sorted_dims = sorted(
            [(label, int(scores.get(label, 5))) for _, label, _ in DIMENSIONS_ORDER],
            key=lambda x: x[1], reverse=True
        )
        visual["card_title"] = f"{sorted_dims[0][0]}型学习者"
        visual["strengths"] = [f"{sorted_dims[0][0]}突出", f"{sorted_dims[1][0]}良好"]
        visual["growth_areas"] = [f"{sorted_dims[-1][0]}可加强"]

    return {"report": report, "visual": visual, "profile": profile}
