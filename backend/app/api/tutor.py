"""智能辅导 API — 多轮对话 + SSE流式 + 画像关联"""

import json
import time
import random
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.agents.tutor_agent import (
    build_tutor_messages, stream_tutor_answer,
    check_follow_up_relevance, build_profile_context,
)
from app.database import query, execute, insert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tutor", tags=["tutor"])


# ─── 数据模型 ────────────────────────────────────────

class ChatRequest(BaseModel):
    user_id: int
    session_id: int | None = None
    message: str
    mode: str = "text"
    parent_id: str | None = None


class FeedbackRequest(BaseModel):
    user_id: int
    session_id: int
    qa_id: str
    helpful: bool


# ─── 会话管理 ────────────────────────────────────────

@router.get("/sessions")
def list_sessions(user_id: int):
    """列出用户所有辅导会话"""
    rows = query(
        "SELECT id, messages, created_at, updated_at FROM chat_sessions "
        "WHERE user_id = %s AND session_type = 'tutoring' ORDER BY updated_at DESC",
        (user_id,)
    )
    sessions = []
    for r in rows:
        msgs = json.loads(r["messages"]) if isinstance(r["messages"], str) else r["messages"]
        # 取最后一个问题作为预览
        preview = ""
        for m in reversed(msgs):
            if m.get("role") == "user":
                preview = m["content"][:50]
                break
        if not preview and msgs:
            preview = msgs[0].get("content", "")[:50]
        sessions.append({
            "id": r["id"],
            "preview": preview or "新对话",
            "message_count": len(msgs),
            "created_at": str(r["created_at"]),
            "updated_at": str(r["updated_at"]),
        })
    return {"sessions": sessions}


@router.post("/sessions/new")
def new_session(user_id: int):
    """新建辅导会话"""
    sid = insert("chat_sessions", {
        "user_id": user_id,
        "session_type": "tutoring",
        "messages": json.dumps([], ensure_ascii=False),
    })
    return {"session_id": sid}


# ─── 历史记录 ────────────────────────────────────────

@router.get("/history")
def get_history(user_id: int, session_id: int):
    """获取指定会话的QA历史"""
    rows = query("SELECT messages FROM chat_sessions WHERE id = %s AND user_id = %s", (session_id, user_id))
    if not rows:
        return {"messages": []}
    msgs = json.loads(rows[0]["messages"]) if isinstance(rows[0]["messages"], str) else rows[0]["messages"]
    return {"messages": msgs}


# ─── 核心：流式对话 ────────────────────────────────────

@router.post("/chat")
def tutor_chat(req: ChatRequest):
    """发送消息并流式返回AI回答"""
    uid = req.user_id
    sid = req.session_id
    question = req.message.strip()
    mode = req.mode
    parent_id = req.parent_id

    if not question:
        return {"error": "消息不能为空"}

    # 获取或创建会话
    if sid:
        rows = query("SELECT messages FROM chat_sessions WHERE id = %s", (sid,))
        messages_history = json.loads(rows[0]["messages"]) if rows else []
    else:
        sid = insert("chat_sessions", {
            "user_id": uid,
            "session_type": "tutoring",
            "messages": json.dumps([], ensure_ascii=False),
        })
        messages_history = []

    # 处理追问上下文
    parent_qa = None
    if parent_id:
        for m in messages_history:
            if m.get("id") == parent_id and m.get("role") == "assistant":
                # 找到对应的用户问题
                idx = messages_history.index(m)
                if idx > 0 and messages_history[idx - 1].get("role") == "user":
                    parent_qa = {
                        "question": messages_history[idx - 1]["content"],
                        "answer": m["content"],
                    }
                break

    # 构建对话历史（供LLM参考）
    conv_history = []
    for m in messages_history[-6:]:
        conv_history.append({"role": m["role"], "content": m["content"]})

    # 构建LLM消息
    llm_messages = build_tutor_messages(
        question=question,
        mode=mode,
        user_id=uid,
        history=conv_history,
        parent_qa=parent_qa,
    )

    # 生成QA ID
    qa_id = f"qa_{int(time.time() * 1000)}_{random.randint(100, 999)}"

    def event_gen():
        full_answer = ""

        # 开始事件
        yield f"data: {json.dumps({'type': 'start', 'qa_id': qa_id, 'mode': mode}, ensure_ascii=False)}\n\n"

        try:
            stream = stream_tutor_answer(llm_messages)
            for chunk in stream:
                delta = chunk.choices[0].delta
                text = delta.content if delta and delta.content else ""
                if text:
                    full_answer += text
                    yield f"data: {json.dumps({'type': 'chunk', 'content': text}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error(f"辅导流式生成失败: {e}")
            error_msg = "抱歉，AI辅导暂时出了点问题，请稍后再试。"
            yield f"data: {json.dumps({'type': 'chunk', 'content': error_msg}, ensure_ascii=False)}\n\n"
            full_answer = error_msg

        # 保存到会话历史
        user_msg = {"role": "user", "content": question, "id": f"u_{qa_id}", "mode": mode, "timestamp": time.time()}
        ai_msg = {"role": "assistant", "content": full_answer, "id": qa_id, "mode": mode, "timestamp": time.time()}
        if parent_id:
            user_msg["parent_id"] = parent_id
            ai_msg["parent_id"] = parent_id

        messages_history.append(user_msg)
        messages_history.append(ai_msg)

        try:
            execute(
                "UPDATE chat_sessions SET messages = %s, updated_at = NOW() WHERE id = %s",
                (json.dumps(messages_history, ensure_ascii=False), sid)
            )
        except Exception as e:
            logger.error(f"保存辅导会话失败: {e}")

        # 完成事件
        yield f"data: {json.dumps({'type': 'done', 'qa_id': qa_id, 'session_id': sid}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─── 反馈 ────────────────────────────────────────

@router.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    """对QA进行点赞/点踩"""
    rows = query("SELECT messages FROM chat_sessions WHERE id = %s", (req.session_id,))
    if not rows:
        return {"error": "会话不存在"}

    msgs = json.loads(rows[0]["messages"]) if isinstance(rows[0]["messages"], str) else rows[0]["messages"]
    for m in msgs:
        if m.get("id") == req.qa_id:
            m["helpful"] = req.helpful
            break

    try:
        execute(
            "UPDATE chat_sessions SET messages = %s WHERE id = %s",
            (json.dumps(msgs, ensure_ascii=False), req.session_id)
        )
    except Exception:
        pass

    return {"status": "ok"}


# ─── 画像关联检查 ────────────────────────────────────

@router.get("/profile-status")
def check_profile(user_id: int):
    """检查用户是否已有画像"""
    ctx = build_profile_context(user_id)
    return {"has_profile": bool(ctx), "preview": ctx[:200] if ctx else ""}
