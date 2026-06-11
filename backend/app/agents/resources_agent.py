"""资源生成路由 — 轻量编排 + 独立窗口调度

职责:
  orchestrate()  → 理解用户需求，决定激活哪些窗口（返回 plan）
  dispatch()     → 并行调用激活的窗口，各自独立执行，收集结果
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.services.llm import chat_deepseek
from app.agents.windows import ensure_registry, get_window, get_window_meta, WINDOW_META

logger = logging.getLogger(__name__)

# 保持与旧接口兼容的元数据导出
AGENT_META = {
    k: {"label": v["label"], "icon": v["icon"]}
    for k, v in WINDOW_META.items()
}

# ─── Orchestrator ──────────────────────────────────────────

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
    """路由规划：理解需求，返回窗口激活计划"""
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
        logger.warning("Orchestrator JSON 解析失败，使用默认 plan")
        return {
            "needs": {"course": "未识别", "topics": [], "level": "初级"},
            "summary": "根据你的需求生成学习资源",
            "agents": [
                {"key": "course", "label": "课程讲解文档",
                 "params": {"title": "学习资料", "topics": [], "focus": "", "level": "初级"}},
                {"key": "mindmap", "label": "知识点思维导图",
                 "params": {"topic": "知识体系", "subtopics": []}},
                {"key": "exercise", "label": "练习题",
                 "params": {"topics": [], "difficulty": "中等", "count": 5}},
            ],
        }


# ─── 窗口调度 ────────────────────────────────────────────

def _run_one_window(agent_cfg: dict) -> tuple[str, dict]:
    """执行单个窗口，返回 (key, result_dict)"""
    key = agent_cfg["key"]
    window = get_window(key)
    if not window:
        return key, {"error": f"未知窗口: {key}", "label": agent_cfg.get("label", key)}

    try:
        result = window.run(agent_cfg.get("params", {}))
        output = result.to_dict()
        output["agent_label"] = agent_cfg.get("label", key)
        return key, output
    except Exception as e:
        logger.error(f"窗口 {key} 执行异常: {e}")
        return key, {
            "type": key,
            "label": agent_cfg.get("label", key),
            "error": str(e),
        }


def dispatch(plan: dict) -> dict[str, dict]:
    """并行调度所有激活的窗口，各自独立执行。

    每个窗口内部有自己的重试/回退/校验逻辑，
    一个窗口失败不影响其他窗口。
    """
    agents = plan.get("agents", [])
    if not agents:
        return {}

    # 确保 Window 注册表已初始化
    ensure_registry()

    results: dict[str, dict] = {}
    logger.info(f"调度 {len(agents)} 个窗口: {[a['key'] for a in agents]}")

    with ThreadPoolExecutor(max_workers=len(agents)) as executor:
        futures = {executor.submit(_run_one_window, cfg): cfg["key"] for cfg in agents}
        for future in as_completed(futures):
            key, result = future.result()
            results[key] = result
            status = "✗" if "error" in result else "✓"
            logger.info(f"  [{status}] {key}: {result.get('title', result.get('label', ''))}")

    return results


def dispatch_streaming(plan: dict, on_event):
    """流式调度：逐个启动窗口并通过回调推送事件。

    on_event(event_type: str, data: dict) 在每个窗口开始/完成时调用。
    用于 SSE 端点。
    """
    agents = plan.get("agents", [])
    if not agents:
        on_event("all_done", {"summary": "无可用窗口", "results": {}})
        return {}

    ensure_registry()
    results: dict[str, dict] = {}

    # 先推送所有 agent_start 事件
    for cfg in agents:
        on_event("agent_start", {
            "agent": cfg["key"],
            "label": cfg.get("label", cfg["key"]),
        })

    # 并行执行
    with ThreadPoolExecutor(max_workers=len(agents)) as executor:
        futures = {executor.submit(_run_one_window, cfg): cfg for cfg in agents}
        for future in as_completed(futures):
            cfg = futures[future]
            key, result = future.result()
            results[key] = result
            if "error" in result:
                on_event("agent_error", {
                    "agent": key,
                    "error": result.get("error", "未知错误"),
                })
            else:
                on_event("agent_done", {
                    "agent": key,
                    "label": result.get("agent_label", key),
                    "result": result,
                })

    on_event("all_done", {"results": results})
    return results
