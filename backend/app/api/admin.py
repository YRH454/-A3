"""管理员 API：用户管理、系统统计"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from app.database import query, execute
from app.utils.auth import decode_token

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def verify_admin(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "未登录")
    payload = decode_token(authorization[7:])
    if not payload or payload.get("role") != "admin":
        raise HTTPException(403, "需要管理员权限")
    return int(payload["sub"])


# ---- Stats ----
@router.get("/stats")
def get_stats(admin_id: int = None):
    """系统统计数据"""
    if admin_id:
        verify_admin_from_id(admin_id)

    total_users = query("SELECT COUNT(*) as c FROM users WHERE is_active=TRUE")[0]["c"]
    total_admins = query("SELECT COUNT(*) as c FROM users WHERE role='admin'")[0]["c"]
    total_guests = query("SELECT COUNT(*) as c FROM guest_sessions")[0]["c"]
    total_resources = query("SELECT COUNT(*) as c FROM learning_resources")[0]["c"]
    total_sessions = query("SELECT COUNT(*) as c FROM chat_sessions WHERE is_active=TRUE")[0]["c"]
    recent_users = query(
        "SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC LIMIT 5"
    )

    return {
        "stats": {
            "total_users": total_users,
            "total_admins": total_admins,
            "total_guests": total_guests,
            "total_resources": total_resources,
            "active_sessions": total_sessions,
        },
        "recent_users": recent_users,
    }


def verify_admin_from_id(admin_id: int):
    rows = query("SELECT role FROM users WHERE id=%s AND is_active=TRUE", (admin_id,))
    if not rows or rows[0]["role"] != "admin":
        raise HTTPException(403, "需要管理员权限")


# ---- User Management ----
@router.get("/users")
def list_users(search: str = "", page: int = 1, page_size: int = 20):
    """用户列表（分页+搜索）"""
    offset = (page - 1) * page_size
    if search:
        rows = query(
            "SELECT id, username, email, role, is_active, created_at FROM users "
            "WHERE username LIKE %s OR email LIKE %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (f"%{search}%", f"%{search}%", page_size, offset)
        )
        total = query(
            "SELECT COUNT(*) as c FROM users WHERE username LIKE %s OR email LIKE %s",
            (f"%{search}%", f"%{search}%")
        )[0]["c"]
    else:
        rows = query(
            "SELECT id, username, email, role, is_active, created_at FROM users ORDER BY created_at DESC LIMIT %s OFFSET %s",
            (page_size, offset)
        )
        total = query("SELECT COUNT(*) as c FROM users")[0]["c"]

    return {"users": rows, "total": total, "page": page, "page_size": page_size}


class UpdateUserRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None


@router.put("/users/{user_id}")
def update_user(user_id: int, req: UpdateUserRequest):
    """修改用户角色或状态"""
    if req.role and req.role not in ("guest", "user", "admin"):
        raise HTTPException(400, "无效的角色")

    updates = []
    params = []
    if req.role is not None:
        updates.append("role = %s")
        params.append(req.role)
    if req.is_active is not None:
        updates.append("is_active = %s")
        params.append(req.is_active)

    if not updates:
        return {"status": "no changes"}

    params.append(user_id)
    execute(f"UPDATE users SET {', '.join(updates)} WHERE id = %s", tuple(params))
    return {"status": "updated", "user_id": user_id}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin_id: int = None):
    """软删除用户"""
    execute("UPDATE users SET is_active = FALSE WHERE id = %s", (user_id,))
    return {"status": "deactivated", "user_id": user_id}


# ---- Guest Management ----
@router.get("/guests")
def list_guests():
    rows = query(
        "SELECT id, session_token, remaining_questions, created_at, expires_at FROM guest_sessions ORDER BY created_at DESC LIMIT 50"
    )
    return {"guests": rows, "total": len(rows)}
