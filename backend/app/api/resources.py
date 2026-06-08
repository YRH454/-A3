"""资源生成 API — 多智能体协同编排"""
import json
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.resources_agent import orchestrate, run_agents, AGENT_RUNNERS, AGENT_META
from app.services.resources_db import (
    init_tables, create_package, save_package_resources, get_package,
    list_packages, create_media_record, get_media_by_package,
    get_resource_session, save_resource_session, list_resource_sessions,
)
from app.services.profile_db import get_chat_session_by_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/resources", tags=["resources"])

init_tables()


# ─── 会话管理 ────────────────────────────────────────

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


# ─── 核心生成 ────────────────────────────────────────

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


class GenerateRequest(BaseModel):
    user_id: int
    message: str = ""
    session_id: int = None


@router.get("/generate/stream")
def generate_stream(user_id: int, session_id: int = None):
    """SSE流式生成：实时推送每个Agent的完成状态"""
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
        from concurrent.futures import ThreadPoolExecutor, as_completed

        agents = plan.get("agents", [])
        yield f"data: {json.dumps({'type': 'plan', 'plan': plan, 'available_agents': AGENT_META}, ensure_ascii=False)}\n\n"

        def run_one(cfg):
            runner = AGENT_RUNNERS.get(cfg["key"])
            if not runner:
                return cfg["key"], {"error": f"未知Agent: {cfg['key']}", "label": cfg.get("label", cfg["key"])}
            try:
                result = runner(cfg.get("params", {}))
                result["agent_label"] = cfg.get("label", cfg["key"])
                return cfg["key"], result
            except Exception as e:
                return cfg["key"], {"error": str(e), "label": cfg.get("label", cfg["key"])}

        # 一次性并行执行所有Agent
        for cfg in agents:
            yield f"data: {json.dumps({'type': 'agent_start', 'agent': cfg['key'], 'label': cfg.get('label', cfg['key'])}, ensure_ascii=False)}\n\n"

        results = {}
        with ThreadPoolExecutor(max_workers=len(agents)) as executor:
            futures = {executor.submit(run_one, cfg): cfg["key"] for cfg in agents}
            for future in as_completed(futures):
                key, result = future.result()
                results[key] = result
                if "error" in result:
                    yield f"data: {json.dumps({'type': 'agent_error', 'agent': key, 'error': result.get('error')}, ensure_ascii=False)}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'agent_done', 'agent': key, 'label': result.get('agent_label', key), 'result': result}, ensure_ascii=False)}\n\n"

        # 保存
        package_id = create_package(user_id, plan.get("needs", {}), plan, [a["key"] for a in agents])
        save_package_resources(package_id, results, "done")

        summary = f"已为你生成 {len(results)} 种学习资源：{'、'.join(AGENT_META.get(k, {}).get('label', k) for k in results)}"
        messages.append({"role": "assistant", "content": summary})
        save_resource_session(user_id, messages, session_id)

        yield f"data: {json.dumps({'type': 'all_done', 'package_id': package_id, 'summary': summary, 'results': results}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.post("/generate")
def generate_sync(req: GenerateRequest):
    """同步生成：编排 + 全部Agent执行完成"""
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

    results = run_agents(plan)

    package_id = create_package(req.user_id, plan.get("needs", {}), plan, [a["key"] for a in agents])
    save_package_resources(package_id, results, "done")

    summary = f"已为你生成 {len(results)} 种学习资源：{'、'.join(AGENT_META.get(k, {}).get('label', k) for k in results)}"
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
