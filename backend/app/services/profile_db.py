"""学生画像数据库操作"""
import json
from app.database import query, execute


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


def save_chat_session(user_id: int, messages: list, session_type: str = "profile_building"):
    existing = get_chat_session(user_id, session_type)
    msg_json = json.dumps(messages, ensure_ascii=False)
    if existing:
        execute(
            "UPDATE chat_sessions SET messages = %s, updated_at = NOW() WHERE id = %s",
            (msg_json, existing["id"])
        )
        return existing["id"]
    else:
        return execute(
            "INSERT INTO chat_sessions (user_id, session_type, messages) VALUES (%s, %s, %s)",
            (user_id, session_type, msg_json)
        )
