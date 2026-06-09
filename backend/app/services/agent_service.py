"""
Agent Service — FastGPT-style Agent for profile building + resource generation
"""
import json
from app.agents.agent_loop import Tool, ToolRegistry, Planner, run_agent_loop
from app.agents.tools import (
    ask_dimension, extract_profile_dimension, generate_report,
    search_learning_resources, final_answer,
)

SYSTEM_PROMPT = """你是学境(Scholarium)的学习助手。你的核心能力是通过对话构建学生画像，然后生成个性化学习方案。

## 可用工具
- ask_dimension: 向学生提问某个学习维度
- extract_profile_dimension: 从学生的回答中提取画像数据
- generate_report: 所有维度收集完毕后，生成最终画像报告
- search_learning_resources: 搜索学习资源（课程、视频、文章）
- final_answer: 直接回答学生问题

## 工作流程
1. 了解学生：通过 ask_dimension 逐一了解7个维度：
   知识基础(knowledge_base)、学习风格(learning_style)、学习难点(weak_points)、
   兴趣方向(interests)、学习目标(goals)、学习节奏(learning_pace)、交互偏好(interaction_pref)

2. 收集信息：
   - 每次只问1个维度
   - 学生回答后，用 extract_profile_dimension 提取关键信息
   - 全部收集完毕后用 generate_report 生成报告

3. 提供资源：
   - 报告生成后，根据学生兴趣和目标用 search_learning_resources 搜索合适的学习资源
   - 搜索结果以友好格式呈现

4. 对话风格：
   - 像了解学生的导师，自然亲切
   - 不要同时问多个问题
   - 简要总结提取到的信息再问下一个维度
"""


def create_agent_tools(user_message: str) -> ToolRegistry:
    """创建工具注册表"""
    registry = ToolRegistry()

    registry.register(Tool(
        "ask_dimension",
        "向学生提问一个画像维度。每次只问1个维度",
        {
            "dim_key": {"type": "string", "description": "维度key，如 knowledge_base"},
            "dim_label": {"type": "string", "description": "维度中文名，如 知识基础"},
            "question": {"type": "string", "description": "具体问题"},
        },
        ask_dimension,
    ))

    registry.register(Tool(
        "extract_profile_dimension",
        "从学生的回答中提取某个维度的画像描述",
        {
            "dim_key": {"type": "string", "description": "维度key"},
            "dim_label": {"type": "string", "description": "维度中文名"},
            "user_text": {"type": "string", "description": "学生的原话"},
        },
        extract_profile_dimension,
    ))

    registry.register(Tool(
        "generate_report",
        "所有7个维度收集完毕后生成最终画像报告",
        {
            "profile_text": {"type": "string", "description": "已收集的画像维度数据"},
        },
        generate_report,
    ))

    registry.register(Tool(
        "search_learning_resources",
        "搜索适合学生的学习资源",
        {
            "topic": {"type": "string", "description": "学习主题"},
            "type": {"type": "string", "description": "资源类型: all, courses, books, videos, articles"},
        },
        search_learning_resources,
    ))

    registry.register(Tool(
        "final_answer",
        "直接回答学生问题，无需调用其他工具",
        {
            "text": {"type": "string", "description": "回答文本"},
        },
        final_answer,
    ))

    return registry


def build_profile_agent(user_message: str) -> tuple[ToolRegistry, Planner]:
    """构建画像 Agent 的工具和计划"""
    registry = create_agent_tools(user_message)
    planner = Planner()

    # 判断是否需要画像构建
    profile_keywords = ["画像", "了解我", "评估", "测试", "profile", "assess"]
    resource_keywords = ["推荐", "资源", "课程", "学习路径", "学什么", "怎么学", "路线", "视频",
                        "教程", "资料", "路径", "计划", "方案"]

    need_profile = any(kw in user_message for kw in profile_keywords)
    need_resources = any(kw in user_message for kw in resource_keywords)

    # 新用户或没有关键词 → 默认走画像构建流程
    if not need_profile and not need_resources:
        need_profile = True

    if need_profile and need_resources:
        planner.set_plan(["了解学习背景", "评估各维度", "生成画像", "搜索资源"])
    elif need_profile:
        planner.set_plan(["了解学习背景", "评估各维度", "生成画像"])
    else:
        planner.set_plan(["理解需求", "搜索资源", "整理推荐"])

    return registry, planner


def run_agent(
    user_message: str,
    conversation: list = None,
    on_event=None,
) -> dict:
    """运行 Agent"""
    registry, planner = build_profile_agent(user_message)

    # 如果有历史对话，注入上下文
    prompt = SYSTEM_PROMPT
    if conversation:
        conv_summary = "\n".join(
            f"{'学生' if m['role'] == 'user' else 'AI'}：{m.get('content', '')[:100]}"
            for m in conversation[-6:]
        )
        prompt += f"\n\n## 对话历史\n{conv_summary}"

    return run_agent_loop(
        user_message=user_message,
        system_prompt=prompt,
        registry=registry,
        planner=planner,
        on_event=on_event,
        max_rounds=10,
    )
