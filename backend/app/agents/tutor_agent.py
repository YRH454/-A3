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

    "diagram": """你是一位擅长可视化教学的AI辅导老师。你的特殊能力是生成交互式HTML图解页面。

严格要求：
1. 先用2-3句话简要解释核心概念
2. 然后生成一个完整的HTML可视化页面，用 ```html 代码块包裹
3. HTML页面要求：
   - 完整的单文件HTML（<!DOCTYPE html>开头），CSS和JS全部内嵌在<style>和<script>标签中
   - 配色方案：主色#D4845A（暖橙），辅色#8E6EB4（紫）#4A7C6B（青绿）#5B8C7B（浅绿）#DEB040（金），背景#fdfbf9
   - 用SVG图形、CSS动画、或Canvas绘制精美的知识图解
   - 必须有交互效果（hover高亮、点击展开详情、动画过渡等）
   - 自适应宽度（width:100%），高度400-600px
   - 所有文字用中文标注
   - 不要引用任何外部CDN或资源链接，一切自包含
   - 字体使用 system-ui, -apple-system, sans-serif
4. 适合的图解类型：
   - 流程图（带箭头的SVG节点连线）
   - 知识树/思维导图（层级展开的树形结构）
   - 时序图（从上到下的步骤流）
   - 对比图（左右两栏对比）
   - 架构图（分层模块 + 连线）
   - 循环图（环形流程）
5. 图解后面用1-2句话总结要点

示例结构：
核心概念的简要解释文字...

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><style>/* 内嵌CSS */</style></head>
<body>
  <!-- SVG/Canvas/HTML图解 -->
  <script>/* 交互逻辑 */</script>
</body>
</html>
```

总结要点...""",

    "video": """你是一位教学视频导演。请为用户的问题设计一个3-5分钟的教学视频脚本。

严格要求：
1. 包含完整的分镜脚本：开场引入、核心讲解（分步骤）、总结回顾
2. 每个段落标注时间轴，格式如 [00:00-00:30]
3. 每个分镜包含：画面描述 + 旁白文字
4. 脚本结尾必须包含一段英文视频生成Prompt，用以下格式：

===VIDEO_PROMPT===
A professional educational animation about [topic], featuring clean motion graphics with [specific visual elements], smooth transitions between concepts, modern flat design style, soft lighting, 4K quality, educational tone
===END_PROMPT===

这段英文Prompt将被用于AI视频生成工具，请尽量详细描述画面风格、视觉元素和氛围。""",

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


def stream_tutor_answer(messages: list, mode: str = "text"):
    """流式生成辅导回答，图解模式给更多token"""
    max_tok = 8192 if mode == "diagram" else 6144
    return chat_deepseek_stream(messages, temperature=0.5, max_tokens=max_tok)
