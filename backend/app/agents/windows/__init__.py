"""独立资源生成窗口 — 每个窗口自治：自选模型、自管容错

使用延迟导入避免循环依赖，通过 ensure_registry() 初始化所有窗口。
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.agents.windows.base import BaseWindow

# 窗口元数据（始终可用，无导入依赖）
WINDOW_META: dict[str, dict] = {
    "course":    {"key": "course",    "label": "课程讲解文档",   "icon": "book"},
    "mindmap":   {"key": "mindmap",   "label": "知识点思维导图", "icon": "tree"},
    "exercise":  {"key": "exercise",  "label": "练习题",        "icon": "edit"},
    "reading":   {"key": "reading",   "label": "拓展阅读材料",   "icon": "glasses"},
    "media":     {"key": "media",     "label": "教学视频脚本",   "icon": "video"},
}

_registry: dict[str, "BaseWindow"] = {}
_initialized = False


def ensure_registry() -> dict[str, "BaseWindow"]:
    """延迟初始化窗口注册表（首次调用时导入所有窗口）"""
    global _registry, _initialized
    if not _initialized:
        from app.agents.windows.course import CourseWindow
        from app.agents.windows.mindmap import MindmapWindow
        from app.agents.windows.exercise import ExerciseWindow
        from app.agents.windows.reading import ReadingWindow
        from app.agents.windows.media import MediaWindow

        _registry = {
            "course": CourseWindow(),
            "mindmap": MindmapWindow(),
            "exercise": ExerciseWindow(),
            "reading": ReadingWindow(),
            "media": MediaWindow(),
        }
        _initialized = True
    return _registry


def get_window(key: str):
    """根据 key 获取窗口实例"""
    return ensure_registry().get(key)


def get_window_meta(key: str) -> dict:
    """获取窗口元数据"""
    return WINDOW_META.get(key, {})


__all__ = [
    "WINDOW_META",
    "ensure_registry",
    "get_window",
    "get_window_meta",
]
