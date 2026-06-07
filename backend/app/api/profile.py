"""学生画像 API 路由"""
import json, asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.profile_agent import (
    profile_graph, ProfileState, _format_profile_summary
)
from app.services.profile_db import (
    get_profile, save_profile, save_chat_session, get_chat_session,
)

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


class ChatRequest(BaseModel):
    user_id: int
    message: str


class ProfileResponse(BaseModel):
    user_id: int
    stage: str
    reply: str
    profile: dict | None = None
    summary: str | None = None


@router.post("/chat", response_model=ProfileResponse)
def profile_chat(req: ChatRequest):
    """非流式对话（备用）"""
    sess = get_chat_session(req.user_id)
    messages = sess["messages"] if sess else []

    messages.append({"role": "user", "content": req.message})

    initial_state: ProfileState = {
        "messages": messages,
        "stage": "greeting" if not sess else "greeting",
        "profile": {},
        "collected_dimensions": [],
        "user_id": req.user_id,
    }

    result = profile_graph.invoke(initial_state)

    save_chat_session(req.user_id, result["messages"])
    if result.get("profile"):
        profile_id = save_profile(req.user_id, result["profile"])

    filled = sum(1 for v in result.get("profile", {}).values() if v and v.strip())
    summary = _format_profile_summary(result["profile"]) if result.get("profile") else None

    return ProfileResponse(
        user_id=req.user_id,
        stage=result.get("stage", "greeting"),
        reply=result["messages"][-1]["content"],
        profile=result.get("profile"),
        summary=summary,
    )


@router.get("/chat/stream")
async def profile_chat_stream(user_id: int, message: str):
    """SSE 流式对话"""
    sess = get_chat_session(user_id)
    messages = sess["messages"] if sess else []
    messages.append({"role": "user", "content": message})

    initial_state: ProfileState = {
        "messages": messages,
        "stage": "greeting" if not sess else "greeting",
        "profile": sess.get("profile", {}) if sess else {},
        "collected_dimensions": [],
        "user_id": user_id,
    }

    async def event_stream():
        # Run in background thread to not block
        result = profile_graph.invoke(initial_state)
        reply = result["messages"][-1]["content"]

        # Save
        save_chat_session(user_id, result["messages"])
        if result.get("profile"):
            save_profile(user_id, result["profile"])

        # Send complete response
        summary = _format_profile_summary(result["profile"]) if result.get("profile") else None
        yield f"data: {json.dumps({'stage': result.get('stage'), 'reply': reply, 'profile': result.get('profile'), 'summary': summary}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{user_id}")
def get_user_profile(user_id: int):
    """获取用户画像"""
    profile = get_profile(user_id)
    if not profile:
        return {"user_id": user_id, "profile": None, "exists": False}
    return {"user_id": user_id, "profile": profile["profile"], "exists": True, "updated_at": profile["updated_at"]}


@router.delete("/{user_id}/reset")
def reset_profile(user_id: int):
    """重置画像，重新构建"""
    from app.database import execute
    execute("UPDATE chat_sessions SET is_active = FALSE WHERE user_id = %s AND session_type = 'profile_building'", (user_id,))
    return {"user_id": user_id, "status": "reset"}
