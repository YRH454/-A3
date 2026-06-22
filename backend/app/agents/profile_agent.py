"""学生画像智能体 — 逐维度提问，DeepSeek对话+千问生成画像"""

import json
import re
import math
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

# ========== P0-1: 垃圾输入双层检测（参考 a3-platform） ==========

_GARBAGE_BLACKLIST = {'asdf', 'qwer', 'zxcv', 'hjkl', 'test', 'aaa', 'bbb', 'abc', 'xxx', '111', '222', '333', '123', '666', '888', '999'}

def detect_garbage_input(text: str, prev_text: str = "") -> dict:
    """双层垃圾检测：代码预筛 + 返回检测结果供 AI 精判
    返回 {"suspicious": bool, "reason": str}
    """
    text = text.strip()
    if not text:
        return {"suspicious": True, "reason": "空输入"}

    # 1. 纯数字/符号
    if re.fullmatch(r'[\d\s\W]+', text):
        return {"suspicious": True, "reason": "纯数字或符号"}

    # 2. 极短输入（<2个有意义字符）
    meaningful = re.sub(r'[\s\d\W]', '', text)
    if len(meaningful) < 2:
        return {"suspicious": True, "reason": "内容过短"}

    # 3. 键盘乱按（黑名单匹配）
    lower = text.lower().strip()
    if lower in _GARBAGE_BLACKLIST:
        return {"suspicious": True, "reason": "疑似键盘乱按"}

    # 4. 纯英文字母 2-8 字符且无常见英文词
    if re.fullmatch(r'[a-zA-Z]{2,8}', text) and text.lower() not in {'ai', 'ml', 'dl', 'ok', 'yes', 'no', 'python', 'java', 'react', 'vue', 'web', 'app'}:
        return {"suspicious": True, "reason": "疑似无意义英文"}

    # 5. 重复上一轮
    if prev_text and text.strip() == prev_text.strip():
        return {"suspicious": True, "reason": "与上次输入完全相同"}

    # 6. 高熵检测（>20字符无中文无英语单词）
    has_chinese = bool(re.search(r'[一-鿿]', text))
    if len(text) > 20 and not has_chinese:
        chars = list(text.lower())
        freq = {}
        for c in chars:
            freq[c] = freq.get(c, 0) + 1
        entropy = -sum((v/len(chars)) * math.log2(v/len(chars)) for v in freq.values())
        if entropy > 3.8:
            return {"suspicious": True, "reason": "高熵乱码"}

    return {"suspicious": False, "reason": ""}


# ========== P0-2: 防重复提问铁律 + 跨维度推断 ==========

QUESTION_PROMPT = """你是一个学习顾问，正在逐步了解学生。

【已收集信息】
{asked_summary}

【铁律——必须遵守】
A. 已收集的维度绝不再追问，直接跳到下一个未了解的维度
B. 学生刚回答过的内容不要重复追问
C. 简单回答直接提取（如"看视频"→学习风格=视觉型；"每周3小时"→学习节奏=慢速）
D. 一句话可能覆盖多个维度，注意跨维度推断
E. 追问要口语化、自然，给2-3个选项提示
F. 每次只问1个维度，不要一次问多个

学生刚才回答了关于「{prev_label}」的问题：{prev_answer}

你必须做到：
1. 先用1句话简短回应学生（表示你在听）
2. 自然过渡到下一个话题：{dim_label}（{dim_desc}）
3. 用友好的语气提出问题，给出2-3个方向提示

控制在2-4句话，像真正聊天一样。"""

EXTRACT_PROMPT = """根据学生的回答，提取「{dim_label}」维度的画像描述。

对话上下文：{context}
学生最新回答：{answer}

【跨维度推断规则】
- "每周X小时" → 同时可推断 learning_pace
- "看视频/B站" → 同时可推断 learning_style=视觉型
- "考研/找工作" → 同时可推断 goals
- "XX很难/不会XX" → 同时可推断 weak_points

请用一句话总结学生在「{dim_label}」这个维度上的特征。
如果能推断出其他维度信息，也一并返回。

返回JSON：
{{"{dim_key}": "特征描述"}}
如果还能推断其他维度，格式如：
{{"{dim_key}": "特征描述", "其他维度key": "推断描述"}}"""


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
    """从学生的回答中提取该维度的特征描述（支持跨维度推断）
    返回主维度的值。跨维度推断的结果存在 _last_extra_dims 中供调用方使用。
    """
    global _last_extra_dims
    _last_extra_dims = {}

    context = "\n".join(
        f"{'学生' if m['role'] == 'user' else 'AI'}：{m['content']}"
        for m in conversation[-6:]
    )

    # 主力模型：DeepSeek
    try:
        resp = chat_deepseek([{
            "role": "system",
            "content": EXTRACT_PROMPT.format(
                dim_label=dim_label, dim_key=dim_key,
                context=context, answer=user_answer,
            )
        }], temperature=0.3, max_tokens=300, json_mode=True)
        text = resp.choices[0].message.content.strip()
    except Exception:
        # P0-3: AI降级 — DeepSeek 失败时用 Qwen 兜底
        try:
            resp = chat_qwen([{
                "role": "system",
                "content": EXTRACT_PROMPT.format(
                    dim_label=dim_label, dim_key=dim_key,
                    context=context, answer=user_answer,
                )
            }], temperature=0.3, max_tokens=300, json_mode=True)
            text = resp.choices[0].message.content.strip()
        except Exception:
            text = ""

    try:
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("\n", 1)[0]
        data = json.loads(text)
        extracted = data.get(dim_key, "").strip()

        # 收集跨维度推断结果
        valid_keys = {k for k, _, _ in DIMENSIONS_ORDER}
        for k, v in data.items():
            if k != dim_key and k in valid_keys and isinstance(v, str) and v.strip():
                _last_extra_dims[k] = v.strip()

        if extracted:
            return extracted
    except (json.JSONDecodeError, KeyError):
        pass

    # 兜底：用用户原话
    if user_answer and len(user_answer) > 2:
        return f"学生提到：{user_answer[:100]}"
    return None

# 跨维度推断结果缓存
_last_extra_dims: dict = {}

def get_extra_dimensions() -> dict:
    """获取上一次 extract 中跨维度推断出的额外维度"""
    return _last_extra_dims


# ========== 多模型并行生成 ==========

import re as _re
from concurrent.futures import ThreadPoolExecutor, as_completed

def generate_final_profile(profile: dict, conversation: list) -> dict:
    """DeepSeek + Qwen 双模型并行生成 — 速度更快，结果更丰富"""
    conv_text = "\n".join(
        f"{'学生' if m['role'] == 'user' else 'AI'}：{m['content']}"
        for m in conversation
    )

    profile_lines = []
    for k, label, _ in DIMENSIONS_ORDER:
        val = profile.get(k, "")
        profile_lines.append(f"- {label}：{val}" if val else f"- {label}：待了解")
    profile_text = "\n".join(profile_lines)

    # ===== 并行任务1：DeepSeek 生成文字报告 + 评分 =====
    def call_deepseek():
        resp = chat_deepseek([{
            "role": "system",
            "content": f"""你是学习画像分析师。请根据学生数据生成报告和评分。

学生数据：
{profile_text}

对话记录（摘要）：
{conv_text[:2000]}

请严格按格式输出（用 ===SECTION=== 分隔）：

===REPORT===
（纯文本报告）

### 学习画像总览
2-3句话概括学习特质，用第二人称

### 多维分析
每个维度1-2句分析

### 个性化学习建议
3条具体可执行建议

===SCORES===
（纯JSON，7个维度1-10分，根据学生实际回答质量打分，避免全部中等分）
{{"知识基础": 8, "学习风格": 7, "学习难点": 5, "兴趣方向": 9, "学习目标": 8, "学习节奏": 7, "交互偏好": 6}}"""
        }], temperature=0.6, max_tokens=2500)
        text = resp.choices[0].message.content.strip()
        report = _extract_section(text, "REPORT")
        report = _re.sub(r'```[^`]*```', '', report)
        report = _re.sub(r'\n\s*\n\s*\n', '\n\n', report).strip()

        scores = {}
        scores_text = _extract_section(text, "SCORES")
        try: scores = json.loads(scores_text)
        except Exception: pass

        return {"report": report, "scores": scores}

    # ===== 并行任务2：Qwen 生成可视化数据 =====
    def call_qwen():
        resp = chat_qwen([{
            "role": "system",
            "content": f"""你是视觉设计师。根据学生画像数据生成可视化配置。

学生数据：
{profile_text}

请严格按格式输出（用 ===SECTION=== 分隔）：

===VISUAL===
（纯JSON）
{{
    "card_title": "一句话标签（如：夜读型AI探索者）",
    "atmosphere": "视觉氛围描述",
    "strengths": ["优势1", "优势2"],
    "growth_areas": ["成长方向1", "成长方向2"],
    "learning_quote": "适合的学习格言"
}}

===RADAR===
（纯JSON，7维度0-1的值）
{{
    "indicator": [{{"name": "知识基础", "max": 1}}, ...共7个],
    "value": [0.8, 0.7, 0.3, 0.9, 0.8, 0.7, 0.6]
}}

===RESOURCES===
（纯JSON数组，5个具体学习资源）
[{{"title": "资源名称", "type": "课程/书籍/视频/工具/社区", "url": "", "why": "推荐理由", "difficulty": "入门/中级/高级"}}]

===ROADMAP===
（纯JSON数组，3-5步学习路线）
[{{"step": 1, "title": "阶段名称", "duration": "建议时长", "focus": "本阶段重点", "milestone": "阶段成果"}}]

===TAGS===
（纯JSON数组，5-8个标签词）
["标签1", "标签2"]"""
        }], temperature=0.7, max_tokens=2000, json_mode=False)

        text = resp.choices[0].message.content.strip()
        visual = {"card_title": "", "atmosphere": "", "strengths": [], "growth_areas": [], "learning_quote": ""}
        try:
            v = json.loads(_extract_section(text, "VISUAL"))
            if isinstance(v, dict): visual.update(v)
        except Exception: pass

        radar = {"indicator": [], "value": []}
        try:
            radar = json.loads(_extract_section(text, "RADAR"))
        except Exception: pass

        resources, roadmap, tags = [], [], []
        try: resources = json.loads(_extract_section(text, "RESOURCES"))
        except Exception: pass
        try: roadmap = json.loads(_extract_section(text, "ROADMAP"))
        except Exception: pass
        try: tags = json.loads(_extract_section(text, "TAGS"))
        except Exception: pass

        visual["radar_data"] = radar
        visual["resources"] = resources
        visual["roadmap"] = roadmap
        visual["tags"] = tags

        return {"visual": visual}

    # ===== 并行执行 =====
    ds_result = {"report": "", "scores": {}}
    qw_result = {"visual": {"card_title": "", "atmosphere": "", "strengths": [], "growth_areas": [], "learning_quote": "", "radar_data": {"indicator": [], "value": []}, "resources": [], "roadmap": [], "tags": []}}

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(call_deepseek): "deepseek",
            executor.submit(call_qwen): "qwen",
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                result = future.result()
                if key == "deepseek":
                    ds_result = result
                else:
                    qw_result = result
            except Exception as e:
                logger = __import__('logging').getLogger(__name__)
                logger.error(f"{key} 并行任务失败: {e}")

    # ===== 合并结果 =====
    report = ds_result["report"]
    scores = ds_result["scores"]
    visual = qw_result["visual"]

    # Fallback: 如果某个模型失败，用兜底数据
    if not report:
        report = f"## 学习画像报告\n\n你的学习画像已生成。各维度评分如下。"
    if not scores:
        for k, label, _ in DIMENSIONS_ORDER:
            val = profile.get(k, "")
            scores[label] = min(9, max(3, len(val) // 8 + 5)) if val else 4
    if not visual.get("radar_data") or not visual["radar_data"].get("value"):
        vals = []
        for _, label, _ in DIMENSIONS_ORDER:
            s = scores.get(label, 5)
            vals.append(s / 10)
            visual["radar_data"]["indicator"].append({"name": label, "max": 1})
        visual["radar_data"]["value"] = vals

    # 确保 visual 包含 scores
    visual["radar_scores"] = scores

    # Fallback: 补充缺失的 visual 字段
    if not visual.get("card_title"):
        sorted_dims = sorted(
            [(label, int(scores.get(label, 5))) for _, label, _ in DIMENSIONS_ORDER],
            key=lambda x: x[1], reverse=True
        )
        visual["card_title"] = f"{sorted_dims[0][0]}型学习者" if sorted_dims else "探索型学习者"
    if not visual.get("strengths"):
        visual["strengths"] = [f"{sorted_dims[0][0]}突出" if sorted_dims else "潜力优秀"]
    if not visual.get("growth_areas"):
        visual["growth_areas"] = [f"{sorted_dims[-1][0]}可加强" if sorted_dims else "持续成长"]

    return {"report": report, "visual": visual, "profile": profile}


def _extract_section(text: str, tag: str) -> str:
    m = _re.search(rf'==={tag}===\s*\n?(.*?)(?=\n===|\Z)', text, _re.DOTALL)
    return m.group(1).strip() if m else ""
