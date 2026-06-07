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

QUESTION_PROMPT = """你是一个学习顾问，正在逐维度了解学生。当前要问的维度是「{dim_label}」（{dim_desc}）。

{asked_summary}

请用自然友好的语气，问一个关于这个维度的问题。要求：
- 直接切入主题，不要铺垫太多
- 如果学生之前提到过相关内容，可以引用
- 1-2句话即可
- 不要评价学生的回答是否正确，只管收集信息"""

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
                           conversation: list, profile: dict) -> str:
    """AI针对特定维度问一个问题"""
    # 总结已了解的维度
    asked_parts = []
    for k, label, _ in DIMENSIONS_ORDER:
        if k in profile and profile[k]:
            asked_parts.append(f"已了解{label}：{profile[k]}")
        elif k == dim_key:
            break  # 当前维度，准备问
    asked_summary = "\n".join(asked_parts) if asked_parts else "尚未收集任何信息"

    resp = chat_deepseek([{
        "role": "system",
        "content": QUESTION_PROMPT.format(
            dim_label=dim_label, dim_desc=dim_desc,
            asked_summary=asked_summary,
        )
    }, {
        "role": "user",
        "content": f"请就「{dim_label}」这个维度向学生提问",
    }], temperature=0.8, max_tokens=200)

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


# ========== 千问负责：生成最终画像报告 ==========

def generate_final_profile(profile: dict, conversation: list) -> dict:
    """千问基于所有收集到的数据，生成完整的画像报告+可视化建议"""
    conv_text = "\n".join(
        f"{'学生' if m['role'] == 'user' else 'AI'}：{m['content']}"
        for m in conversation
    )

    # 整理收集到的画像数据
    profile_lines = []
    for k, label, desc in DIMENSIONS_ORDER:
        val = profile.get(k, "")
        status = val if val else "待了解"
        profile_lines.append(f"- {label}：{status}")
    profile_text = "\n".join(profile_lines)

    resp = chat_qwen([{
        "role": "system",
        "content": f"""你是一个专业的学习画像分析师。根据收集到的学生数据，生成一份个性化学习画像报告。

学生画像数据：
{profile_text}

对话记录：
{conv_text}

请生成一份结构化的画像报告，包含以下部分：

## 学习画像总览
用2-3句话概括这位学生的学习特质

## 各维度详细分析
每个维度写1-2句话分析

## 学习建议
基于画像给出3条具体的学习建议

## 可视化建议（JSON）
返回一个JSON，描述适合这个画像的可视化方式：
{{"radar_scores": {{"知识基础": 分数1-10, "学习风格": ..., "学习难点": ..., "兴趣方向": ..., "学习目标": ..., "学习节奏": ..., "交互偏好": ...}},
 "primary_color": "适合的配色主题",
 "summary_tag": "一句话标签"}}

报告语气温暖专业，用第二人称"你"。"""
    }], temperature=0.7, max_tokens=2048)

    report = resp.choices[0].message.content.strip()

    # 尝试提取JSON可视化数据
    visual = None
    try:
        # Find JSON block
        if "```json" in report:
            json_str = report.split("```json")[1].split("```")[0]
        elif "```" in report:
            json_str = report.split("```")[1].split("```")[0]
        else:
            json_str = report
        visual = json.loads(json_str)
    except Exception:
        radar = {}
        for k, label, _ in DIMENSIONS_ORDER:
            val = profile.get(k, "") or ""
            radar[label] = min(8, len(val) // 10 + 3) if val else 3
        visual = {
            "radar_scores": radar,
            "primary_color": "暖色系",
            "summary_tag": "学习者",
        }

    return {"report": report, "visual": visual, "profile": profile}
