"""课程讲解窗口 — 结构化 Markdown 讲义生成

首选 Claude（结构化长文本最优），回退 DeepSeek。
可选接入教材 RAG 检索增强。
"""

import logging
from app.agents.windows.base import BaseWindow, WindowResult

logger = logging.getLogger(__name__)

COURSE_SYSTEM_PROMPT = """你是资深课程设计师。为以下学生生成一份结构化课程讲解文档。

## 课程信息
- 课程主题：{title}
- 核心知识点：{topics}
- 重点关注：{focus}
- 学生水平：{level}

## 输出要求
- 完整的 Markdown 格式，层次清晰
- 必须包含以下章节：
  ## 学习目标（3-5条具体的可衡量目标）
  ## 核心概念讲解（每个知识点深入讲解，配合例子）
  ## 关键公式/代码（如有）
  ## 本章小结
  ## 思考题（2-3道）
- 语言通俗易懂，多用类比和实例帮助理解
- 适当使用表格、列表、代码块增强可读性
- 长度：1000-2000字
- 直接输出课程内容，不要写"以下是为您生成的文档"之类的套话
- 不要在开头重复标题"""


class CourseWindow(BaseWindow):
    window_key = "course"
    window_label = "课程讲解文档"
    primary_model = "deepseek"   # Phase 6 可切换为 "claude"
    fallback_model = "qwen"
    temperature = 0.5
    max_tokens = 3000
    timeout = 120.0

    def build_prompt(self, params: dict) -> str:
        title = params.get("title", "课程讲解")
        topics = ", ".join(params.get("topics", [])) or "基础知识"
        focus = params.get("focus", "全面理解")
        level = params.get("level", "初级")

        # 可选：注入 RAG 检索到的教材内容
        rag_context = params.get("_rag_context", "")
        base_prompt = COURSE_SYSTEM_PROMPT.format(
            title=title, topics=topics, focus=focus, level=level,
        )
        if rag_context:
            base_prompt += (
                f"\n\n## 参考资料（请优先基于以下材料编写）\n{rag_context}"
            )
        return base_prompt

    def validate(self, result: WindowResult) -> bool:
        content = result.content
        if not content or not isinstance(content, str):
            return False
        # 基本长度检查
        if len(content) < 300:
            logger.warning(f"[course] 内容过短: {len(content)}字")
            return False
        # 基本结构检查：至少有 ## 标题
        if "##" not in content:
            logger.warning("[course] 缺少 Markdown 标题层级")
            return False
        return True

    def post_process(self, result: WindowResult, params: dict) -> WindowResult:
        """课程内容直接就是 Markdown 文本，无需 JSON 解析"""
        result.title = params.get("title", "课程讲解")
        return result
