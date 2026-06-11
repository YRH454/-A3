"""拓展阅读窗口 — 真实搜索 + NotebookLM 式内容合成

流程:
  1. 真实搜索（Perplexity / SerpAPI）→ 获取真实资源列表
  2. LLM 合成 → 整理为结构化推荐（带来源链接）
  3. 如搜索不可用 → 回退纯 LLM 生成（当前方案）

核心理念（NotebookLM 模式）：
  基于真实检索到的素材来生成推荐，而非 LLM 凭记忆编造。
"""

import json
import logging
from app.agents.windows.base import BaseWindow, WindowResult
from app.agents.shared.rag import search_documents, RetrievalContext

logger = logging.getLogger(__name__)

# ─── 纯 LLM 生成提示词（回退方案）───────────────────────

READING_FALLBACK_PROMPT = """你是学术导师。为学习以下内容的学生推荐拓展阅读材料。

学习主题：{topic}
当前水平：{level}
兴趣方向：{interest}

请推荐 3-5 篇拓展资料，按推荐阅读顺序排列。

要求：
- Markdown 格式
- 每篇包含：标题（含作者/来源）、类型（论文/书籍/博文/教程）、核心观点、推荐理由
- 难度递进，从入门到进阶
- 直接输出内容"""

# ─── NotebookLM 式合成提示词 ────────────────────────────

READING_SYNTHESIS_PROMPT = """你是学术导师。根据搜索到的真实资源，为学生整理一份结构化拓展阅读推荐。

## 学生信息
- 学习主题：{topic}
- 当前水平：{level}
- 兴趣方向：{interest}

## 检索到的资源素材
{search_context}

## 任务
基于上述真实资源，编写一份个性化阅读推荐。要求：

1. **筛选与排序**：从搜索结果中选出 3-5 个最适合学生水平和兴趣的资源
2. **按难度递进排列**：从入门到进阶
3. **每篇推荐包含**：
   - 标题（保持原文标题，可加中文译注）
   - 类型标签（📄论文 / 📚书籍 / 📝博文 / 🎥教程 / 🌐在线课程）
   - 核心观点（1-2句，基于搜索摘要提炼）
   - 推荐理由（为什么适合这位学生，1-2句）
   - 来源链接（如果有URL）
4. **开头**：2-3句总体推荐说明
5. **结尾**：建议的阅读顺序和学习方法

输出格式：标准 Markdown，直接输出内容。"""


class ReadingWindow(BaseWindow):
    window_key = "reading"
    window_label = "拓展阅读材料"
    primary_model = "deepseek"   # 用于合成推荐文本
    fallback_model = "qwen"
    temperature = 0.5
    max_tokens = 2500
    json_mode = False
    timeout = 90.0

    # 是否启用真实搜索（可通过环境变量关闭，强制回退纯 LLM）
    enable_search: bool = True

    def build_prompt(self, params: dict) -> str:
        topic = params.get("topic", "当前学习内容")
        level = params.get("level", "初级")
        interest = params.get("interest", "")

        # ── 尝试真实搜索 ──
        search_context = ""
        if self.enable_search:
            try:
                query = f"学习资源推荐 {topic} {level}水平 教程 书籍 论文"
                retrieval: RetrievalContext = search_documents(query, top_k=5)
                if retrieval.results:
                    search_context = retrieval.to_prompt_text(max_results=5)
                    logger.info(f"[reading] 检索到 {len(retrieval.results)} 条结果, 来源={retrieval.source_description}")
                    # 将检索结果存入 params 供 base 层使用
                    params["_search_context"] = search_context
                    params["_has_search_results"] = True
            except Exception as e:
                logger.warning(f"[reading] 搜索异常，回退纯 LLM: {e}")

        # ── 选择提示词 ──
        if search_context:
            return READING_SYNTHESIS_PROMPT.format(
                topic=topic, level=level, interest=interest or "不限",
                search_context=search_context,
            )
        else:
            return READING_FALLBACK_PROMPT.format(
                topic=topic, level=level, interest=interest or "不限",
            )

    def validate(self, result: WindowResult) -> bool:
        content = result.content
        if not content or not isinstance(content, str):
            return False

        # 基本长度检查
        if len(content) < 200:
            logger.warning(f"[reading] 内容过短: {len(content)}字")
            return False

        # 至少有一条推荐（以 "- " 或 "1. " 开头的行）
        lines = content.split("\n")
        recommendation_lines = [
            l for l in lines
            if l.strip().startswith(("- ", "1. ", "2. ", "3. ", "**"))
        ]
        if len(recommendation_lines) < 2:
            logger.warning(f"[reading] 推荐条目过少: {len(recommendation_lines)}")
            # 不阻塞，内容可能仍然是好的

        return True

    def post_process(self, result: WindowResult, params: dict) -> WindowResult:
        result.title = params.get("topic", "拓展阅读推荐")

        # 标注是否有真实搜索结果
        if params.get("_has_search_results"):
            result.metadata["search_backed"] = True
            result.metadata["source"] = "真实搜索 + AI 合成"
        else:
            result.metadata["search_backed"] = False
            result.metadata["source"] = "AI 知识库生成"

        return result
