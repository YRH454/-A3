"""资源生成数据库操作"""
import json
from app.database import query, execute, insert


def init_tables():
    """初始化资源生成相关表"""
    execute("""
        CREATE TABLE IF NOT EXISTS resource_packages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            session_id INT,
            needs_summary JSON,
            generation_plan JSON,
            resources JSON,
            status VARCHAR(20) DEFAULT 'draft',
            enabled_agents JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)
    execute("""
        CREATE TABLE IF NOT EXISTS generated_media (
            id INT AUTO_INCREMENT PRIMARY KEY,
            package_id INT NOT NULL,
            script TEXT,
            seedance_prompt TEXT,
            video_url VARCHAR(500),
            status VARCHAR(20) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)


def create_package(user_id: int, needs_summary: dict, plan: dict, enabled_agents: list) -> int:
    return insert("resource_packages", {
        "user_id": user_id,
        "needs_summary": json.dumps(needs_summary, ensure_ascii=False),
        "generation_plan": json.dumps(plan, ensure_ascii=False),
        "enabled_agents": json.dumps(enabled_agents, ensure_ascii=False),
        "status": "generating",
    })


def save_package_resources(package_id: int, resources: dict, status: str = "done"):
    execute(
        "UPDATE resource_packages SET resources = %s, status = %s, updated_at = NOW() WHERE id = %s",
        (json.dumps(resources, ensure_ascii=False), status, package_id)
    )


def update_package_status(package_id: int, status: str):
    execute(
        "UPDATE resource_packages SET status = %s, updated_at = NOW() WHERE id = %s",
        (status, package_id)
    )


def get_package(package_id: int) -> dict | None:
    rows = query("SELECT * FROM resource_packages WHERE id = %s", (package_id,))
    if not rows:
        return None
    r = rows[0]
    return _row_to_dict(r)


def list_packages(user_id: int) -> list:
    rows = query(
        "SELECT * FROM resource_packages WHERE user_id = %s ORDER BY updated_at DESC",
        (user_id,)
    )
    return [_row_to_dict(r) for r in rows]


def _row_to_dict(r: dict) -> dict:
    def _json(v):
        return json.loads(v) if isinstance(v, str) else v

    return {
        "id": r["id"],
        "user_id": r["user_id"],
        "session_id": r.get("session_id"),
        "needs_summary": _json(r.get("needs_summary", "{}")),
        "generation_plan": _json(r.get("generation_plan", "{}")),
        "resources": _json(r.get("resources", "{}")),
        "status": r.get("status", "draft"),
        "enabled_agents": _json(r.get("enabled_agents", "[]")),
        "created_at": str(r.get("created_at", "")),
        "updated_at": str(r.get("updated_at", "")),
    }


# ─── 媒体记录 ────────────────────────────────────────

def create_media_record(package_id: int, script: str = "", seedance_prompt: str = "") -> int:
    return insert("generated_media", {
        "package_id": package_id,
        "script": script,
        "seedance_prompt": seedance_prompt,
        "status": "script_done",
    })


def update_media_video(media_id: int, video_url: str, status: str = "done"):
    execute(
        "UPDATE generated_media SET video_url = %s, status = %s WHERE id = %s",
        (video_url, status, media_id)
    )


def get_media_by_package(package_id: int) -> dict | None:
    rows = query(
        "SELECT * FROM generated_media WHERE package_id = %s ORDER BY id DESC LIMIT 1",
        (package_id,)
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "id": r["id"],
        "package_id": r["package_id"],
        "script": r.get("script", ""),
        "seedance_prompt": r.get("seedance_prompt", ""),
        "video_url": r.get("video_url", ""),
        "status": r.get("status", "pending"),
        "created_at": str(r.get("created_at", "")),
    }


# ─── 会话复用 ────────────────────────────────────────

def get_resource_session(user_id: int) -> dict | None:
    rows = query(
        "SELECT * FROM chat_sessions WHERE user_id = %s AND session_type = 'resource_generation' "
        "AND is_active = TRUE ORDER BY updated_at DESC LIMIT 1",
        (user_id,)
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "id": r["id"],
        "user_id": r["user_id"],
        "messages": json.loads(r["messages"]) if isinstance(r["messages"], str) else r["messages"],
    }


def save_resource_session(user_id: int, messages: list, session_id: int = None) -> int:
    msg_json = json.dumps(messages, ensure_ascii=False)
    if session_id:
        execute("UPDATE chat_sessions SET messages = %s, updated_at = NOW() WHERE id = %s", (msg_json, session_id))
        return session_id
    existing = get_resource_session(user_id)
    if existing:
        execute("UPDATE chat_sessions SET messages = %s, updated_at = NOW() WHERE id = %s", (msg_json, existing["id"]))
        return existing["id"]
    return insert("chat_sessions", {
        "user_id": user_id,
        "session_type": "resource_generation",
        "messages": msg_json,
    })


def list_resource_sessions(user_id: int) -> list:
    rows = query(
        "SELECT id, messages, created_at, updated_at, is_active "
        "FROM chat_sessions WHERE user_id = %s AND session_type = 'resource_generation' "
        "ORDER BY updated_at DESC", (user_id,)
    )
    result = []
    for r in rows:
        msgs = json.loads(r["messages"]) if isinstance(r["messages"], str) else r["messages"]
        preview = ""
        for m in msgs:
            if m["role"] == "assistant":
                preview = m["content"][:50]
                break
        result.append({
            "id": r["id"],
            "preview": preview or "新会话",
            "message_count": len(msgs),
            "is_active": bool(r["is_active"]),
            "created_at": str(r["created_at"]),
            "updated_at": str(r["updated_at"]),
        })
    return result
