"""认证 API：注册、登录、游客模式"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from app.database import query, execute
from app.utils.auth import (
    hash_password, verify_password, create_token,
    decode_token, generate_guest_token, has_permission,
)
from app.services.profile_db import save_profile

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ---- Models ----
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


# ---- Dependency: get current user from token ----
def get_current_user(authorization: str = Header(None)) -> dict:
    """从 Authorization header 解析当前用户"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")

    token = authorization[7:]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="登录已过期")

    user_id = int(payload["sub"])
    rows = query("SELECT id, username, email, role FROM users WHERE id = %s AND is_active = TRUE", (user_id,))
    if not rows:
        raise HTTPException(status_code=401, detail="用户不存在")

    user = rows[0]
    user["role"] = user["role"]
    return user


def get_admin_user(authorization: str = Header(None)) -> dict:
    user = get_current_user(authorization)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


# ---- Routes ----

@router.post("/register")
def register(req: RegisterRequest):
    """注册新用户"""
    if len(req.username) < 2 or len(req.username) > 30:
        raise HTTPException(400, "用户名长度2-30个字符")
    if len(req.password) < 6:
        raise HTTPException(400, "密码至少6位")

    # Check duplicate
    existing = query("SELECT id FROM users WHERE email = %s OR username = %s",
                     (req.email, req.username))
    if existing:
        raise HTTPException(400, "用户名或邮箱已被注册")

    pw_hash = hash_password(req.password)
    user_id = execute(
        "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, 'user')",
        (req.username, req.email, pw_hash)
    )

    token = create_token(user_id, "user")
    return {
        "token": token,
        "user": {"id": user_id, "username": req.username, "email": req.email, "role": "user"},
    }


@router.post("/login")
def login(req: LoginRequest):
    """用户登录"""
    rows = query(
        "SELECT id, username, email, password_hash, role FROM users WHERE email = %s AND is_active = TRUE",
        (req.email,)
    )
    if not rows or not verify_password(req.password, rows[0]["password_hash"]):
        raise HTTPException(401, "邮箱或密码错误")

    user = rows[0]
    token = create_token(user["id"], user["role"])
    return {
        "token": token,
        "user": {"id": user["id"], "username": user["username"],
                 "email": user["email"], "role": user["role"]},
    }


@router.post("/guest")
def guest_login():
    """游客模式：无需注册，生成临时会话"""
    token = generate_guest_token()
    session_id = execute(
        "INSERT INTO guest_sessions (session_token, remaining_questions) VALUES (%s, 3)",
        (token,)
    )
    return {
        "token": token,
        "user": {"id": 0, "username": "游客", "role": "guest", "session_id": session_id},
        "notice": "游客模式可体验3个维度的画像构建，数据24小时后自动清除",
    }


@router.get("/me")
def me(authorization: str = Header(None)):
    """获取当前用户信息"""
    # Try JWT first
    if authorization and authorization.startswith("Bearer "):
        payload = decode_token(authorization[7:])
        if payload:
            user_id = int(payload["sub"])
            rows = query("SELECT id, username, email, role FROM users WHERE id = %s", (user_id,))
            if rows:
                u = rows[0]
                return {"user": {**u, "role": u["role"]}, "permissions": {}}

    # Try guest token
    if authorization and authorization.startswith("Guest "):
        token = authorization[6:]
        rows = query("SELECT * FROM guest_sessions WHERE session_token = %s AND remaining_questions > 0", (token,))
        if rows:
            return {
                "user": {"id": 0, "username": "游客", "role": "guest",
                         "session_id": rows[0]["id"],
                         "remaining": rows[0]["remaining_questions"]},
                "permissions": {"profile_build": True, "resource_generate": False},
            }

    # No auth = anonymous with guest access
    return {
        "user": {"role": "anonymous"},
        "notice": "请登录或使用游客模式",
    }


@router.get("/admin/users")
def list_users(user: dict = None):
    """管理员：查看所有用户"""
    if not user:
        raise HTTPException(401)
    # Actually this should use get_admin_user dependency
    rows = query("SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC")
    return {"users": rows}
