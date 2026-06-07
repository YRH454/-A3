from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.profile import router as profile_router
from app.api.auth import router as auth_router
from app.api.admin import router as admin_router

app = FastAPI(
    title="个性化学习智能体系统",
    description="基于大模型的个性化资源生成与学习多智能体系统 - A3赛题",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router)
app.include_router(auth_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {"message": "个性化学习智能体系统 API", "version": "0.1.0"}


@app.get("/health")
def health():
    from app.database import query
    try:
        query("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}
