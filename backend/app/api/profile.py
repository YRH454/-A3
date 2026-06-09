"""学生画像 API — 逐维度提问，实时画像更新"""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.profile_agent import (
    DIMENSIONS_ORDER, PROFILE_DIMENSIONS,
    get_next_dimension, ask_dimension_question,
    extract_dimension_answer, generate_final_profile,
)
from app.services.profile_db import (
    get_profile, save_profile, get_chat_session, save_chat_session,
    get_profile_sessions, get_chat_session_by_id,
)

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


# ─── 会话管理 ────────────────────────────────────────

@router.get("/sessions")
def list_sessions(user_id: int):
    return {"user_id": user_id, "sessions": get_profile_sessions(user_id)}


@router.post("/sessions/new")
def new_session(user_id: int):
    from app.database import execute
    execute("UPDATE chat_sessions SET is_active = FALSE WHERE user_id = %s AND session_type = 'profile_building' AND is_active = TRUE", (user_id,))
    return {"status": "ready"}


# ─── 画像构建 ────────────────────────────────────────

@router.post("/start")
def start_profile(user_id: int, session_id: int = None):
    # 恢复指定会话
    if session_id:
        sess = get_chat_session_by_id(session_id)
        if sess and sess.get("messages") and len(sess["messages"]) > 0:
            profile = sess.get("profile", {})
            filled = {k for k, v in profile.items() if v and v.strip() and not k.startswith("__")}
            dim = get_next_dimension(filled)
            if dim:
                last_ai = next((m["content"] for m in reversed(sess["messages"]) if m["role"] == "assistant"), sess["messages"][-1]["content"])
                return {"reply": last_ai, "messages": sess["messages"], "session_id": session_id, "current_dim": {"key": dim["key"], "label": dim["label"]}, "profile": profile, "filled": len(filled), "total": len(DIMENSIONS_ORDER), "done": False}
            return {"reply": sess["messages"][-1]["content"], "messages": sess["messages"], "session_id": session_id, "current_dim": None, "profile": profile, "filled": len(DIMENSIONS_ORDER), "total": len(DIMENSIONS_ORDER), "done": True}

    # 不带session_id = 创建全新会话
    from app.database import execute
    execute("UPDATE chat_sessions SET is_active = FALSE WHERE user_id = %s AND session_type = 'profile_building' AND is_active = TRUE", (user_id,))

    dim = DIMENSIONS_ORDER[0]
    key, label, desc = dim
    question = ask_dimension_question(key, label, desc, [], {})
    messages = [{"role": "assistant", "content": question}]
    sid = save_chat_session(user_id, messages)
    return {"reply": question, "messages": messages, "session_id": sid, "current_dim": {"key": key, "label": label}, "profile": {}, "filled": 0, "total": len(DIMENSIONS_ORDER), "done": False}


class ChatRequest(BaseModel):
    user_id: int
    message: str
    session_id: int | None = None


@router.post("/chat")
def profile_chat(req: ChatRequest):
    sess = get_chat_session_by_id(req.session_id) if req.session_id else get_chat_session(req.user_id)
    sid = sess["id"] if sess else None
    messages = sess["messages"] if sess else []
    profile = sess.get("profile", {}) if sess else {}

    filled = {k for k, v in profile.items() if v and v.strip()}
    dim = get_next_dimension(filled)

    if dim is None:
        full = generate_final_profile(profile, messages)
        messages.append({"role": "user", "content": req.message})
        messages.append({"role": "assistant", "content": full["report"]})
        save_chat_session(req.user_id, messages, session_id=sid)
        save_profile(req.user_id, full["profile"])
        return {"reply": full["report"], "profile": full["profile"], "visual": full.get("visual"), "current_dim": None, "filled": len(filled), "total": len(DIMENSIONS_ORDER), "done": True}

    messages.append({"role": "user", "content": req.message})
    extracted = extract_dimension_answer(dim["key"], dim["label"], messages, req.message)
    # 无论如何都要填充维度，不能卡住
    profile[dim["key"]] = extracted or f"学生简答：{req.message[:80]}"
    filled.add(dim["key"])

    next_dim = get_next_dimension(filled)
    if next_dim is None:
        full = generate_final_profile(profile, messages)
        messages.append({"role": "assistant", "content": full["report"]})
        save_chat_session(req.user_id, messages, session_id=sid)
        save_profile(req.user_id, full["profile"])
        return {"reply": full["report"], "profile": full["profile"], "visual": full.get("visual"), "current_dim": None, "filled": len(filled), "total": len(DIMENSIONS_ORDER), "done": True}

    question = ask_dimension_question(next_dim["key"], next_dim["label"], next_dim["desc"],
        messages, profile, prev_label=dim["label"], prev_answer=req.message)
    messages.append({"role": "assistant", "content": question})
    save_chat_session(req.user_id, messages, session_id=sid)
    save_profile(req.user_id, profile)
    return {"reply": question, "profile": profile, "current_dim": {"key": next_dim["key"], "label": next_dim["label"]}, "filled": len(filled), "total": len(DIMENSIONS_ORDER), "done": False}


@router.get("/{user_id}")
def get_user_profile(user_id: int):
    """获取用户画像"""
    p = get_profile(user_id)
    if not p:
        return {"user_id": user_id, "profile": None, "exists": False}
    return {
        "user_id": user_id,
        "profile": p["profile"],
        "filled": sum(1 for v in p["profile"].values() if v and v.strip()),
        "total": len(DIMENSIONS_ORDER),
        "exists": True,
        "updated_at": p["updated_at"],
    }


@router.delete("/{user_id}/reset")
def reset_profile(user_id: int):
    from app.database import execute
    execute(
        "UPDATE chat_sessions SET is_active = FALSE "
        "WHERE user_id = %s AND session_type = 'profile_building'",
        (user_id,)
    )
    return {"user_id": user_id, "status": "reset"}


@router.get("/meta/dimensions")
def get_dimensions():
    return {"dimensions": {k: v for k, v in PROFILE_DIMENSIONS.items()}}


# ─── Agent Stream ──────────────────────────────────────

@router.post("/chat/agent")
def profile_chat_agent_sync(req: ChatRequest):
    """Agent Loop（同步版，调试用）"""
    from app.services.agent_service import run_agent
    events = []
    result = run_agent(req.message, on_event=lambda e, d: events.append({"event": e, "data": d}))
    return {"status": result["status"], "answer": result.get("answer", ""),
            "rounds": result["rounds"], "events": events}


# ─── Agent SSE Stream ───────────────────────────────────

from fastapi.responses import StreamingResponse
import asyncio
import threading

@router.post("/chat/agent")
async def profile_chat_agent(req: ChatRequest):
    """SSE 流式 Agent Loop —— LLM 自主决定工具调用顺序"""
    from app.services.agent_service import run_agent

    async def generate():
        # Send start immediately to prevent client timeout
        yield f"data: {json.dumps({'event': 'start', 'data': {}})}\n\n"

        queue = asyncio.Queue()
        done = threading.Event()

        def on_event(evt: str, data: dict):
            try:
                loop = asyncio.get_event_loop()
                loop.call_soon_threadsafe(queue.put_nowait, {"event": evt, "data": data})
            except Exception:
                pass

        def run_blocking():
            try:
                result = run_agent(req.message, on_event=on_event)
                loop = asyncio.get_event_loop()
                loop.call_soon_threadsafe(queue.put_nowait, {"event": "__done__", "data": result})
            except Exception as e:
                loop = asyncio.get_event_loop()
                loop.call_soon_threadsafe(queue.put_nowait, {"event": "__error__", "data": str(e)})
            finally:
                done.set()

        t = threading.Thread(target=run_blocking, daemon=True)
        t.start()

        while not done.is_set() or not queue.empty():
            try:
                msg = await asyncio.wait_for(queue.get(), timeout=0.3)
                if msg["event"] == "__done__":
                    yield f"data: {json.dumps({'event': 'done', 'data': msg['data']}, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                    return
                elif msg["event"] == "__error__":
                    yield f"data: {json.dumps({'event': 'error', 'data': msg['data']}, ensure_ascii=False)}\n\n"
                    return
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield ": heartbeat\n\n"
                continue

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
