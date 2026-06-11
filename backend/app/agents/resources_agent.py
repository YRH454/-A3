"""多智能体协同资源生成 — Orchestrator + 5专家Agent"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.services.llm import chat_deepseek

logger = logging.getLogger(__name__)

AGENT_META = {
    "course":    {"label": "课程讲解文档", "icon": "book"},
    "mindmap":   {"label": "知识点思维导图", "icon": "tree"},
    "exercise":  {"label": "练习题", "icon": "edit"},
    "reading":   {"label": "拓展阅读材料", "icon": "glasses"},
    "media":     {"label": "教学视频脚本", "icon": "video"},
    "search":    {"label": "全网课程搜索", "icon": "search"},
}

# ==================== Orchestrator ====================

ORCHESTRATOR_PROMPT = """你是学习资源规划师。根据学生的需求，分析并制定资源生成计划。

学生消息：{user_input}

对话历史：
{history}

请完成：
1. 提取关键信息：专业、课程、知识点、学习目标、薄弱环节、偏好
2. 决定启用哪些资源类型（从以下5种中选择合适的）：
   - course: 结构化课程讲解文档（Markdown）
   - mindmap: 知识点思维导图（Mermaid语法）
   - exercise: 练习题（选择题/简答题/案例分析）
   - reading: 拓展阅读推荐
   - media: 教学视频脚本+分镜
   - search: 全网搜索真实课程/视频/书籍资源（联网）
3. 为每种启用的资源生成具体的生成参数（主题、重点、难度等）

返回纯JSON（不要markdown标记）：
{{
    "needs": {{
        "major": "学生专业",
        "course": "课程名称",
        "topics": ["知识点1", "知识点2"],
        "level": "初级/中级/高级",
        "weak_points": ["薄弱点"],
        "goal": "学习目标",
        "preference": "偏好描述"
    }},
    "summary": "一句话概括需求",
    "agents": [
        {{
            "key": "course",
            "label": "课程讲解文档",
            "params": {{
                "title": "文档标题",
                "topics": ["核心主题"],
                "focus": "重点关注内容",
                "level": "初级/中级/高级"
            }}
        }}
    ]
}}

只返回JSON，不要其他文字。"""


def orchestrate(user_input: str, history: list) -> dict:
    """编排者：理解需求，制定计划"""
    history_text = "\n".join(
        f"{'学生' if m['role'] == 'user' else 'AI'}：{m['content']}"
        for m in history[-8:]
    ) if history else "（首次对话）"

    resp = chat_deepseek([{
        "role": "system",
        "content": ORCHESTRATOR_PROMPT.format(
            user_input=user_input, history=history_text,
        )
    }], temperature=0.3, max_tokens=1500, json_mode=True)

    try:
        raw = resp.choices[0].message.content.strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: return a basic plan
        return {
            "needs": {"course": "未识别", "topics": [], "level": "初级"},
            "summary": "根据你的需求生成学习资源",
            "agents": [
                {"key": "course", "label": "课程讲解文档", "params": {"title": "学习资料", "topics": [], "focus": "", "level": "初级"}},
                {"key": "mindmap", "label": "知识点思维导图", "params": {"topic": "知识体系", "subtopics": []}},
                {"key": "exercise", "label": "练习题", "params": {"topics": [], "difficulty": "中等", "count": 5}},
            ]
        }


# ==================== CourseAgent ====================

COURSE_PROMPT = """你是资深课程设计师。为以下学生生成一份结构化课程讲解文档。

课程主题：{title}
核心知识点：{topics}
重点关注：{focus}
学生水平：{level}

要求：
- Markdown格式，结构清晰
- 包含：学习目标、核心概念讲解（每个知识点）、关键公式/代码、小结、思考题
- 语言通俗易懂，配合例子说明
- 适当使用表格、列表、代码块
- 长度：800-1500字
- 直接输出内容，不要写"以下是为您生成的文档"之类的套话"""


def generate_course(params: dict) -> dict:
    title = params.get("title", "课程讲解")
    topics = ", ".join(params.get("topics", [])) or "基础知识"
    focus = params.get("focus", "全面理解")
    level = params.get("level", "初级")

    resp = chat_deepseek([{
        "role": "system",
        "content": COURSE_PROMPT.format(title=title, topics=topics, focus=focus, level=level)
    }], temperature=0.5, max_tokens=2500)

    return {
        "type": "course",
        "label": "课程讲解文档",
        "title": title,
        "content": resp.choices[0].message.content.strip(),
    }


# ==================== MindMapAgent ====================

MINDMAP_PROMPT = """你是知识结构专家。将知识点组织为层级化思维导图。

主题：{topic}
涉及的知识点：{subtopics}

要求：
- 输出标准 Mermaid mindmap 语法
- 从中心主题向外分3-4层展开
- 每个节点简洁（不超过10字）
- 逻辑层次清晰

输出格式示例：
```mermaid
mindmap
  root((中心主题))
    分支1
      子节点A
      子节点B
    分支2
      子节点C
      子节点D
```

直接输出 Mermaid 代码块，不要额外解释。"""


def generate_mindmap(params: dict) -> dict:
    topic = params.get("topic", "知识体系")
    subtopics = ", ".join(params.get("subtopics", [])) or topic

    resp = chat_deepseek([{
        "role": "system",
        "content": MINDMAP_PROMPT.format(topic=topic, subtopics=subtopics)
    }], temperature=0.4, max_tokens=2000)

    content = resp.choices[0].message.content.strip()
    # 提取 mermaid 代码块
    if "```mermaid" in content:
        start = content.index("```mermaid") + len("```mermaid")
        end = content.index("```", start) if "```" in content[start:] else len(content)
        mermaid_code = content[start:end].strip()
    elif "```" in content:
        start = content.index("```") + 3
        end = content.index("```", start) if "```" in content[start:] else len(content)
        mermaid_code = content[start:end].strip()
    else:
        mermaid_code = content

    return {
        "type": "mindmap",
        "label": "知识点思维导图",
        "title": topic,
        "content": mermaid_code,
    }


# ==================== ExerciseAgent ====================

EXERCISE_PROMPT = """你是命题专家。根据知识点生成练习题。

知识点：{topics}
难度：{difficulty}
题目数量：{count}

请生成{count}道题目，涵盖以下题型：
- choice: 单选题（4选项）
- short_answer: 简答题
- case_analysis: 案例分析题

返回纯JSON（不要markdown标记）：
{{
    "exercises": [
        {{
            "id": "ex001",
            "type": "choice",
            "difficulty": "中等",
            "tags": ["知识点"],
            "question": "题目内容",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "answer": "A",
            "explanation": "解析"
        }}
    ]
}}

只返回JSON，不要其他文字。"""


def generate_exercise(params: dict) -> dict:
    topics = ", ".join(params.get("topics", [])) or "基础知识"
    difficulty = params.get("difficulty", "中等")
    count = params.get("count", 5)

    resp = chat_deepseek([{
        "role": "system",
        "content": EXERCISE_PROMPT.format(topics=topics, difficulty=difficulty, count=count)
    }], temperature=0.3, max_tokens=3000, json_mode=True)

    try:
        data = json.loads(resp.choices[0].message.content.strip())
    except json.JSONDecodeError:
        data = {"exercises": []}

    return {
        "type": "exercise",
        "label": "练习题",
        "title": f"{topics} 练习题",
        "content": data,
    }


# ==================== ReadingAgent ====================

READING_PROMPT = """你是学术导师。为学习以下内容的学生推荐拓展阅读材料。

学习主题：{topic}
当前水平：{level}
兴趣方向：{interest}

请推荐3-5篇拓展资料，按推荐阅读顺序排列。

要求：
- Markdown格式
- 每篇包含：标题（含作者/来源）、类型（论文/书籍/博文/教程）、核心观点、推荐理由
- 难度递进，从入门到进阶
- 直接输出内容"""


def generate_reading(params: dict) -> dict:
    topic = params.get("topic", "当前学习内容")
    level = params.get("level", "初级")
    interest = params.get("interest", "")

    resp = chat_deepseek([{
        "role": "system",
        "content": READING_PROMPT.format(topic=topic, level=level, interest=interest)
    }], temperature=0.5, max_tokens=2000)

    return {
        "type": "reading",
        "label": "拓展阅读材料",
        "title": f"{topic} 拓展阅读推荐",
        "content": resp.choices[0].message.content.strip(),
    }


# ==================== MediaAgent ====================

MEDIA_PROMPT = """你是教学视频导演。为知识点设计3-5分钟的短视频。

主题：{topic}
目标观众：{level}水平学生
重点：{focus}

请生成：
1. 视频脚本（分镜，包含旁白和画面描述）
2. 一段英文AI视频生成Prompt（用于AI视频生成工具）

返回纯JSON（不要markdown标记）：
{{
    "script": "完整的分镜脚本（Markdown格式，含时间轴）",
    "seedance_prompt": "英文AI视频生成Prompt，描述视频风格、场景、氛围"
}}"""


def generate_media(params: dict) -> dict:
    topic = params.get("topic", "学习内容")
    level = params.get("level", "初级")
    focus = params.get("focus", "核心概念")

    resp = chat_deepseek([{
        "role": "system",
        "content": MEDIA_PROMPT.format(topic=topic, level=level, focus=focus)
    }], temperature=0.6, max_tokens=2500, json_mode=True)

    try:
        data = json.loads(resp.choices[0].message.content.strip())
    except json.JSONDecodeError:
        data = {
            "script": "## 视频脚本\n\n脚本生成失败，请重试。",
            "seedance_prompt": "",
        }

    return {
        "type": "media",
        "label": "教学视频脚本",
        "title": f"{topic} 教学视频",
        "content": data,
    }


# ==================== SearchAgent ====================

def generate_search(params: dict) -> dict:
    """联网搜索学习资源"""
    topic = params.get("topic", "")
    keywords = params.get("keywords", topic)
    query = f"优质学习资源推荐：{topic} {keywords} 课程 视频 书籍 教程 2025"

    resp = chat_deepseek([{
        "role": "system",
        "content": f"""你是学习资源搜索专家。请搜索并整理关于以下主题的优质学习资源。

搜索主题：{topic}
关键词：{keywords}

请按以下格式输出搜索结果（Markdown表格）：

## 搜索主题：{topic}

### 📚 推荐课程
| 课程名称 | 平台 | 难度 | 特点 | 链接关键词 |
|---------|------|------|------|-----------|
（3-5个课程）

### 🎬 视频教程
| 视频/系列名 | 平台 | 时长 | 适合人群 | 搜索关键词 |
（3-5个）

### 📖 书籍推荐
| 书名 | 作者 | 难度 | 说明 |
（2-3本）

### 🛠️ 实战项目
| 项目名 | 技术栈 | 难度 | 简介 |
（2-3个）

### 🎯 推荐学习路线
（简短的学习路线建议）

请确保推荐的都是真实存在的优质资源。"""
    }], temperature=0.4, max_tokens=2000, search_enable=True)

    content = resp.choices[0].message.content.strip()
    return {
        "type": "search",
        "label": "全网课程搜索结果",
        "title": f"{topic} 学习资源",
        "content": content,
        "searched": True,
    }


# ==================== Agent 调度 ====================

AGENT_RUNNERS = {
    "course":   generate_course,
    "mindmap":  generate_mindmap,
    "exercise": generate_exercise,
    "reading":  generate_reading,
    "media":    generate_media,
    "search":   generate_search,
}


def run_agents(plan: dict) -> dict:
    """并行执行所有Agent，返回结果字典"""
    agents = plan.get("agents", [])
    if not agents:
        return {}

    results = {}

    def run_one(agent_cfg):
        key = agent_cfg["key"]
        runner = AGENT_RUNNERS.get(key)
        if not runner:
            return key, {"error": f"未知Agent: {key}"}
        try:
            result = runner(agent_cfg.get("params", {}))
            result["agent_label"] = agent_cfg.get("label", key)
            return key, result
        except Exception as e:
            logger.error(f"Agent {key} 失败: {e}")
            return key, {"type": key, "label": agent_cfg.get("label", key), "error": str(e)}

    with ThreadPoolExecutor(max_workers=len(agents)) as executor:
        futures = {executor.submit(run_one, cfg): cfg["key"] for cfg in agents}
        for future in as_completed(futures):
            key, result = future.result()
            results[key] = result

    return results
