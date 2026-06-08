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
    if session_id:
        sess = get_chat_session_by_id(session_id)
        if sess and sess.get("messages") and len(sess["messages"]) > 0:
            profile = sess.get("profile", {})
            filled = {k for k, v in profile.items() if v and v.strip()}
            dim = get_next_dimension(filled)
            if dim:
                last_ai = next((m["content"] for m in reversed(sess["messages"]) if m["role"] == "assistant"), sess["messages"][-1]["content"])
                return {"reply": last_ai, "messages": sess["messages"], "session_id": session_id, "current_dim": {"key": dim["key"], "label": dim["label"]}, "profile": profile, "filled": len(filled), "total": len(DIMENSIONS_ORDER), "done": False}
            return {"reply": sess["messages"][-1]["content"], "messages": sess["messages"], "session_id": session_id, "current_dim": None, "profile": profile, "filled": len(DIMENSIONS_ORDER), "total": len(DIMENSIONS_ORDER), "done": True}

    dim = DIMENSIONS_ORDER[0]
    key, label, desc = dim
    question = ask_dimension_question(key, label, desc, [], {})
    messages = [{"role": "assistant", "content": question}]
    sid = save_chat_session(user_id, messages)
    return {"reply": question, "messages": messages, "session_id": sid, "current_dim": {"key": key, "label": label}, "profile": {}, "filled": 0, "total": len(DIMENSIONS_ORDER), "done": False}


class ChatRequest(BaseModel):
    user_id: int
    message: str
    session_id: int = None


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
    if extracted:
        profile[dim["key"]] = extracted
        filled.add(dim["key"])

    next_dim = get_next_dimension(filled)
    if next_dim is None:
        full = generate_final_profile(profile, messages)
        messages.append({"role": "assistant", "content": full["report"]})
        save_chat_session(req.user_id, messages, session_id=sid)
        save_profile(req.user_id, full["profile"])
        return {"reply": full["report"], "profile": full["profile"], "visual": full.get("visual"), "current_dim": None, "filled": len(filled), "total": len(DIMENSIONS_ORDER), "done": True}

    question = ask_dimension_question(next_dim["key"], next_dim["label"], next_dim["desc"], messages, profile)
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
