"""学生画像数据库操作"""
import json
from app.database import query, execute, insert


def get_profile(user_id: int) -> dict | None:
    rows = query("SELECT * FROM student_profiles WHERE user_id = %s", (user_id,))
    if not rows:
        return None
    row = rows[0]
    return {
        "id": row["id"], "user_id": row["user_id"],
        "profile": json.loads(row["profile_data"]) if isinstance(row["profile_data"], str) else row["profile_data"],
        "version": row["version"], "updated_at": str(row["updated_at"]),
    }


def save_profile(user_id: int, profile_data: dict) -> int:
    existing = query("SELECT id, version FROM student_profiles WHERE user_id = %s", (user_id,))
    profile_json = json.dumps(profile_data, ensure_ascii=False)
    if existing:
        new_ver = existing[0]["version"] + 1
        execute(
            "UPDATE student_profiles SET profile_data = %s, version = %s WHERE user_id = %s",
            (profile_json, new_ver, user_id)
        )
        return existing[0]["id"]
    else:
        return execute(
            "INSERT INTO student_profiles (user_id, profile_data, version) VALUES (%s, %s, 1)",
            (user_id, profile_json)
        )


def save_profile_history(profile_id: int, change_log: dict, trigger: str = "dialogue"):
    execute(
        "INSERT INTO profile_history (profile_id, change_log, trigger_event) VALUES (%s, %s, %s)",
        (profile_id, json.dumps(change_log, ensure_ascii=False), trigger)
    )


def get_chat_session(user_id: int, session_type: str = "profile_building"):
    rows = query(
        "SELECT * FROM chat_sessions WHERE user_id = %s AND session_type = %s AND is_active = TRUE ORDER BY updated_at DESC LIMIT 1",
        (user_id, session_type)
    )
    if not rows:
        return None
    row = rows[0]
    return {
        "id": row["id"], "user_id": row["user_id"],
        "messages": json.loads(row["messages"]) if isinstance(row["messages"], str) else row["messages"],
        "session_type": row["session_type"],
        "profile": _get_profile_dict(user_id),
    }


def get_chat_session_by_id(session_id: int) -> dict | None:
    rows = query("SELECT * FROM chat_sessions WHERE id = %s", (session_id,))
    if not rows:
        return None
    row = rows[0]
    return {
        "id": row["id"], "user_id": row["user_id"],
        "messages": json.loads(row["messages"]) if isinstance(row["messages"], str) else row["messages"],
        "session_type": row["session_type"],
        "is_active": row["is_active"],
    }


def _get_profile_dict(user_id: int) -> dict:
    profile = get_profile(user_id)
    return profile["profile"] if profile else {}


def save_chat_session(user_id: int, messages: list, session_type: str = "profile_building", session_id: int = None):
    msg_json = json.dumps(messages, ensure_ascii=False)
    if session_id:
        execute("UPDATE chat_sessions SET messages = %s, updated_at = NOW() WHERE id = %s", (msg_json, session_id))
        return session_id
    # 无session_id = 创建新会话
    return insert("chat_sessions", {"user_id": user_id, "session_type": session_type, "messages": msg_json})


def get_profile_sessions(user_id: int) -> list:
    rows = query(
        "SELECT id, messages, created_at, updated_at, is_active FROM chat_sessions "
        "WHERE user_id = %s AND session_type = 'profile_building' ORDER BY updated_at DESC",
        (user_id,)
    )
    result = []
    for r in rows:
        msgs = json.loads(r["messages"]) if isinstance(r["messages"], str) else r["messages"]
        preview = ""
        for m in msgs:
            if m["role"] == "assistant":
                preview = m["content"][:40]
                break
        result.append({
            "id": r["id"], "preview": preview or "新会话",
            "message_count": len(msgs), "is_active": bool(r["is_active"]),
            "created_at": str(r["created_at"]), "updated_at": str(r["updated_at"]),
        })
    return result
