"""资源生成 API — 独立窗口架构 + SSE 流式推送"""

import json
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.agents.resources_agent import orchestrate, dispatch, dispatch_streaming, AGENT_META
from app.agents.windows import WINDOW_META, ensure_registry

from app.services.resources_db import (
    init_tables, create_package, save_package_resources, get_package,
    list_packages, create_media_record, get_media_by_package,
    get_resource_session, save_resource_session, list_resource_sessions,
)
from app.services.profile_db import get_chat_session_by_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/resources", tags=["resources"])

init_tables()


# ─── 会话管理 ──────────────────────────────────────────

@router.get("/sessions")
def list_sessions(user_id: int):
    return {"user_id": user_id, "sessions": list_resource_sessions(user_id)}


@router.post("/sessions/new")
def new_session(user_id: int):
    from app.database import execute
    execute(
        "UPDATE chat_sessions SET is_active = FALSE "
        "WHERE user_id = %s AND session_type = 'resource_generation' AND is_active = TRUE",
        (user_id,)
    )
    return {"status": "ready"}


# ─── 核心生成 ──────────────────────────────────────────

class StartRequest(BaseModel):
    user_id: int
    message: str
    session_id: int = None


@router.post("/start")
def start_generation(req: StartRequest):
    """编排阶段：理解学生需求，返回资源生成计划"""
    sess = get_chat_session_by_id(req.session_id) if req.session_id else get_resource_session(req.user_id)
    messages = sess["messages"] if sess else []

    plan = orchestrate(req.message, messages)
    messages.append({"role": "user", "content": req.message})

    agent_labels = [f"  → {a.get('label', a['key'])}" for a in plan.get("agents", [])]
    reply = f"""好的，我理解了你的需求：

{plan.get('summary', '根据你的需求生成学习资源')}

我将为你生成以下资源：
{chr(10).join(agent_labels)}

是否开始生成？你也可以告诉我需要调整的地方。"""

    messages.append({"role": "assistant", "content": reply})
    sid = save_resource_session(req.user_id, messages, session_id=req.session_id)

    return {
        "reply": reply,
        "messages": messages,
        "session_id": sid,
        "plan": plan,
        "available_agents": AGENT_META,
    }


@router.get("/generate/stream")
def generate_stream(user_id: int, session_id: int = None):
    """SSE 流式生成：每个窗口独立执行，实时推送事件。

    事件类型（前端契约不变）：
      plan        → 规划结果
      agent_start → 窗口开始执行
      agent_done  → 窗口完成（含 result）
      agent_error → 窗口失败
      all_done    → 全部完成（含 package_id）
    """
    sess = get_chat_session_by_id(session_id) if session_id else get_resource_session(user_id)
    messages = sess["messages"] if sess else []

    # 提取最后一条用户消息用于编排
    last_user = ""
    for m in reversed(messages):
        if m["role"] == "user":
            last_user = m["content"]
            break

    plan = orchestrate(last_user, messages)

    def event_gen():
        agents = plan.get("agents", [])
        yield f"data: {json.dumps({'type': 'plan', 'plan': plan, 'available_agents': AGENT_META}, ensure_ascii=False)}\n\n"

        # 使用流式调度器：各自独立的窗口，互不干扰
        results = {}
        events_buffer: list[str] = []

        def collect_event(event_type: str, data: dict):
            """收集窗口事件，缓存后逐条 yield"""
            nonlocal results
            if event_type == "agent_done":
                results[data["agent"]] = data.get("result", {})
                events_buffer.append(
                    f"data: {json.dumps({'type': 'agent_done', 'agent': data['agent'], 'label': data.get('label', data['agent']), 'result': data.get('result', {})}, ensure_ascii=False)}\n\n"
                )
            elif event_type == "agent_error":
                results[data["agent"]] = {"error": data.get("error")}
                events_buffer.append(
                    f"data: {json.dumps({'type': 'agent_error', 'agent': data['agent'], 'error': data.get('error')}, ensure_ascii=False)}\n\n"
                )
            elif event_type == "agent_start":
                events_buffer.append(
                    f"data: {json.dumps({'type': 'agent_start', 'agent': data['agent'], 'label': data.get('label', data['agent'])}, ensure_ascii=False)}\n\n"
                )

        # 先发 agent_start 事件
        for cfg in agents:
            yield f"data: {json.dumps({'type': 'agent_start', 'agent': cfg['key'], 'label': cfg.get('label', cfg['key'])}, ensure_ascii=False)}\n\n"

        # 并行调度所有窗口
        dispatch_streaming(plan, collect_event)

        # 推送缓存的事件
        for evt in events_buffer:
            yield evt

        # 保存结果
        package_id = create_package(user_id, plan.get("needs", {}), plan, [a["key"] for a in agents])
        save_package_resources(package_id, results, "done")

        summary = f"已为你生成 {len(results)} 种学习资源：{'、'.join(WINDOW_META.get(k, {}).get('label', k) for k in results)}"
        messages.append({"role": "assistant", "content": summary})
        save_resource_session(user_id, messages, session_id)

        yield f"data: {json.dumps({'type': 'all_done', 'package_id': package_id, 'summary': summary, 'results': results}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.post("/generate")
def generate_sync(req: StartRequest):
    """同步生成：编排 + 全部窗口执行完成"""
    sess = get_chat_session_by_id(req.session_id) if req.session_id else get_resource_session(req.user_id)
    messages = sess["messages"] if sess else []

    if req.message:
        messages.append({"role": "user", "content": req.message})

    last_user = ""
    for m in reversed(messages):
        if m["role"] == "user":
            last_user = m["content"]
            break

    plan = orchestrate(last_user, messages)
    agents = plan.get("agents", [])

    agent_labels = [f"→ {a.get('label', a['key'])}" for a in agents]
    confirm_msg = f"开始生成！将为你准备：\n\n" + "\n".join(agent_labels) + "\n\n请稍候..."
    messages.append({"role": "assistant", "content": confirm_msg})
    sid = save_resource_session(req.user_id, messages, session_id=req.session_id)

    # 独立窗口并行调度
    results = dispatch(plan)

    package_id = create_package(req.user_id, plan.get("needs", {}), plan, [a["key"] for a in agents])
    save_package_resources(package_id, results, "done")

    summary = f"已为你生成 {len(results)} 种学习资源：{'、'.join(WINDOW_META.get(k, {}).get('label', k) for k in results)}"
    messages.append({"role": "assistant", "content": summary})
    save_resource_session(req.user_id, messages, session_id=sid)

    return {
        "reply": summary,
        "messages": messages,
        "session_id": sid,
        "package_id": package_id,
        "plan": plan,
        "results": results,
    }


# ─── 资源包管理 ────────────────────────────────────────

@router.get("/packages")
def list_user_packages(user_id: int):
    return {"user_id": user_id, "packages": list_packages(user_id)}


@router.get("/packages/{package_id}")
def get_resource_package(package_id: int):
    pkg = get_package(package_id)
    if not pkg:
        return {"package_id": package_id, "exists": False}
    return {"package_id": package_id, "exists": True, "package": pkg}


@router.get("/packages/{package_id}/media")
def get_package_media(package_id: int):
    media = get_media_by_package(package_id)
    return {"package_id": package_id, "media": media}


@router.get("/meta/agents")
def get_agents_meta():
    return {"agents": AGENT_META}
