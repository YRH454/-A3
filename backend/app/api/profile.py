"""学生画像 API — 一问一答式对话，AI 主动提问"""
import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.profile_agent import (
    ask_question, extract_current_answer, generate_profile, count_filled, PROFILE_DIMENSIONS,
)
from app.services.profile_db import (
    get_profile, save_profile, get_chat_session, save_chat_session,
)

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


class ChatRequest(BaseModel):
    user_id: int
    message: str


@router.post("/chat")
async def profile_chat(req: ChatRequest):
    """一问一答：AI 主动提问，用户回答，对话结束后自动生成画像"""
    sess = get_chat_session(req.user_id)
    messages = sess["messages"] if sess else []
    profile = sess.get("profile", {}) if sess else {}

    # 添加用户消息
    messages.append({"role": "user", "content": req.message})

    # 增量提取当前回答中的画像信息
    profile = extract_current_answer(messages, profile)
    filled_count = count_filled(profile)

    # AI 判断：继续提问 or 生成画像
    result = ask_question(messages, profile)

    if result["ready"] or filled_count >= 5:
        # 信息够了，生成完整画像
        full = generate_profile(messages)
        profile = full["profile"]
        report = full["report"]

        messages.append({"role": "assistant", "content": report})
        save_chat_session(req.user_id, messages)
        save_profile(req.user_id, profile)

        return {
            "user_id": req.user_id,
            "reply": report,
            "profile": profile,
            "filled": count_filled(profile),
            "total": len(PROFILE_DIMENSIONS),
            "done": True,
        }

    # 还没完，AI 问下一个问题
    question = result["question"]
    messages.append({"role": "assistant", "content": question})
    save_chat_session(req.user_id, messages)
    save_profile(req.user_id, profile)

    return {
        "user_id": req.user_id,
        "reply": question,
        "profile": profile,
        "filled": filled_count,
        "total": len(PROFILE_DIMENSIONS),
        "done": False,
    }


@router.get("/chat/stream")
async def profile_chat_stream(user_id: int, message: str):
    """SSE 流式版本（前端用这个）"""
    import asyncio

    async def event_stream():
        import concurrent.futures
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            sess = get_chat_session(user_id)
            messages = sess["messages"] if sess else []
            profile = sess.get("profile", {}) if sess else {}

            messages.append({"role": "user", "content": message})
            profile = await loop.run_in_executor(pool, extract_current_answer, messages, profile)
            filled_count = count_filled(profile)
            result = await loop.run_in_executor(pool, ask_question, messages, profile)

            if result["ready"] or filled_count >= 5:
                full = await loop.run_in_executor(pool, generate_profile, messages)
                profile = full["profile"]
                report = full["report"]
                messages.append({"role": "assistant", "content": report})
                save_chat_session(user_id, messages)
                save_profile(user_id, profile)

                data = {
                    "reply": report,
                    "profile": profile,
                    "filled": count_filled(profile),
                    "total": len(PROFILE_DIMENSIONS),
                    "done": True,
                }
            else:
                question = result["question"]
                messages.append({"role": "assistant", "content": question})
                save_chat_session(user_id, messages)
                save_profile(user_id, profile)

                data = {
                    "reply": question,
                    "profile": profile,
                    "filled": filled_count,
                    "total": len(PROFILE_DIMENSIONS),
                    "done": False,
                }

        yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
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
    return {
        "user_id": user_id,
        "profile": profile["profile"],
        "filled": count_filled(profile["profile"]),
        "total": len(PROFILE_DIMENSIONS),
        "exists": True,
        "updated_at": profile["updated_at"],
    }


@router.delete("/{user_id}/reset")
def reset_profile(user_id: int):
    """重置画像"""
    from app.database import execute
    execute("UPDATE chat_sessions SET is_active = FALSE WHERE user_id = %s AND session_type = 'profile_building'", (user_id,))
    return {"user_id": user_id, "status": "reset"}


@router.get("/meta/dimensions")
def get_dimensions():
    """返回所有画像维度定义"""
    return PROFILE_DIMENSIONS
