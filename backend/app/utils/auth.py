"""认证工具：密码哈希、JWT、角色权限"""
import hashlib
import secrets
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "role": role, "exp": expire},
        JWT_SECRET, algorithm=JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None


def generate_guest_token() -> str:
    return secrets.token_urlsafe(32)


# ---- Permission Matrix ----
ROLE_PERMISSIONS = {
    "guest": {
        "profile_build": True,      # 可以试用画像（限3维度）
        "resource_generate": False,  # 不能生成资源
        "learning_path": False,      # 不能使用学习路径
        "tutoring": False,           # 不能使用辅导
        "data_save": False,          # 数据不持久化（24h过期）
        "admin_access": False,
    },
    "user": {
        "profile_build": True,
        "resource_generate": True,
        "learning_path": True,
        "tutoring": True,
        "data_save": True,
        "admin_access": False,
    },
    "admin": {
        "profile_build": True,
        "resource_generate": True,
        "learning_path": True,
        "tutoring": True,
        "data_save": True,
        "admin_access": True,
    },
}


def has_permission(role: str, action: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["guest"])
    return perms.get(action, False)
