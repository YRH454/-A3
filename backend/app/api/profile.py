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
)

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.post("/start")
def start_profile(user_id: int):
    """AI 主动问第一个维度的问题"""
    sess = get_chat_session(user_id)

    # 恢复已有会话的进度
    if sess and sess.get("messages") and len(sess["messages"]) > 0:
        profile = sess.get("profile", {})
        filled = {k for k, v in profile.items() if v and v.strip()}
        dim = get_next_dimension(filled)
        if dim:
            question = ask_dimension_question(
                dim["key"], dim["label"], dim["desc"],
                sess["messages"], profile
            )
            return {
                "reply": question,
                "current_dim": {"key": dim["key"], "label": dim["label"]},
                "profile": profile,
                "filled": len(filled),
                "total": len(DIMENSIONS_ORDER),
                "done": False,
            }
        # 所有维度已完成，重置并重新开始
        from app.database import execute
        execute(
            "UPDATE chat_sessions SET is_active = FALSE "
            "WHERE user_id = %s AND session_type = 'profile_building'",
            (user_id,)
        )

    # 全新开始
    dim = DIMENSIONS_ORDER[0]
    key, label, desc = dim
    question = ask_dimension_question(key, label, desc, [], {})

    messages = [{"role": "assistant", "content": question}]
    save_chat_session(user_id, messages)

    return {
        "reply": question,
        "current_dim": {"key": key, "label": label},
        "profile": {},
        "filled": 0,
        "total": len(DIMENSIONS_ORDER),
        "done": False,
    }


class ChatRequest(BaseModel):
    user_id: int
    message: str


@router.post("/chat")
def profile_chat(req: ChatRequest):
    """处理用户回答，提取特征，问下一个维度"""
    sess = get_chat_session(req.user_id)
    messages = sess["messages"] if sess else []
    profile = sess.get("profile", {}) if sess else {}

    # 确定当前在问哪个维度
    filled = {k for k, v in profile.items() if v and v.strip()}
    dim = get_next_dimension(filled)

    if dim is None:
        # 所有维度已覆盖，生成最终画像
        full = generate_final_profile(profile, messages)
        profile = full["profile"]
        report = full["report"]

        messages.append({"role": "user", "content": req.message})
        messages.append({"role": "assistant", "content": report})
        save_chat_session(req.user_id, messages)
        save_profile(req.user_id, profile)

        return {
            "reply": report,
            "profile": profile,
            "visual": full.get("visual"),
            "current_dim": None,
            "filled": len(filled),
            "total": len(DIMENSIONS_ORDER),
            "done": True,
        }

    # 添加用户消息
    messages.append({"role": "user", "content": req.message})

    # 提取当前维度的特征
    extracted = extract_dimension_answer(
        dim["key"], dim["label"], messages, req.message
    )

    if extracted:
        profile[dim["key"]] = extracted
        filled.add(dim["key"])

    # 问下一个维度
    next_dim = get_next_dimension(filled)

    if next_dim is None:
        # 全部问完了，生成最终画像
        full = generate_final_profile(profile, messages)
        profile = full["profile"]
        report = full["report"]

        messages.append({"role": "assistant", "content": report})
        save_chat_session(req.user_id, messages)
        save_profile(req.user_id, profile)

        return {
            "reply": report,
            "profile": profile,
            "visual": full.get("visual"),
            "current_dim": None,
            "filled": len(filled),
            "total": len(DIMENSIONS_ORDER),
            "done": True,
        }

    # 问下一个维度
    question = ask_dimension_question(
        next_dim["key"], next_dim["label"], next_dim["desc"],
        messages, profile
    )
    messages.append({"role": "assistant", "content": question})
    save_chat_session(req.user_id, messages)
    save_profile(req.user_id, profile)

    return {
        "reply": question,
        "profile": profile,
        "current_dim": {"key": next_dim["key"], "label": next_dim["label"]},
        "filled": len(filled),
        "total": len(DIMENSIONS_ORDER),
        "done": False,
    }


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
