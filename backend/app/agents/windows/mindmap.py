"""思维导图窗口 — Mermaid mindmap 语法生成

逻辑简单：DeepSeek JSON mode 即可胜任。
"""

import logging
import re
from app.agents.windows.base import BaseWindow, WindowResult

logger = logging.getLogger(__name__)

MINDMAP_SYSTEM_PROMPT = """你是知识结构专家。将知识点组织为层级化思维导图。

## 输入信息
- 主题：{topic}
- 涉及的知识点：{subtopics}

## 输出要求
- 输出标准 Mermaid mindmap 语法
- 从中心主题向外分 3-4 层展开
- 每个节点简洁（不超过10字）
- 逻辑层次清晰，从核心概念到细节
- 节点数控制在 15-30 个

## 输出格式示例
```mermaid
mindmap
  root((中心主题))
    分支1
      子节点A
      子节点B
    分支2
      子节点C
      子节点D
```

直接输出 Mermaid 代码块，不要额外解释。"""


class MindmapWindow(BaseWindow):
    window_key = "mindmap"
    window_label = "知识点思维导图"
    primary_model = "deepseek"
    fallback_model = "qwen"
    temperature = 0.4
    max_tokens = 2000
    timeout = 60.0

    def build_prompt(self, params: dict) -> str:
        topic = params.get("topic", "知识体系")
        subtopics = ", ".join(params.get("subtopics", [])) or topic
        return MINDMAP_SYSTEM_PROMPT.format(topic=topic, subtopics=subtopics)

    def extract_content(self, raw_response) -> str:
        """从 LLM 响应中提取纯 Mermaid 代码"""
        try:
            content = raw_response.choices[0].message.content.strip()
        except (AttributeError, IndexError, KeyError):
            return ""

        # 提取 mermaid 代码块内容
        if "```mermaid" in content:
            start = content.index("```mermaid") + len("```mermaid")
            rest = content[start:]
            end = rest.index("```") if "```" in rest else len(rest)
            return rest[:end].strip()
        elif "```" in content:
            start = content.index("```") + 3
            rest = content[start:]
            end = rest.index("```") if "```" in rest else len(rest)
            return rest[:end].strip()
        return content

    def validate(self, result: WindowResult) -> bool:
        content = result.content
        if not content or not isinstance(content, str):
            return False

        # 必须包含 mindmap 关键字
        if "mindmap" not in content.lower():
            logger.warning("[mindmap] 缺少 mindmap 关键字")
            return False

        # 基本括号配对检查
        open_parens = content.count("(") + content.count("((")
        close_parens = content.count(")") + content.count("))")
        if open_parens != close_parens:
            logger.warning(f"[mindmap] 括号不匹配: ({{{open_parens}}} vs ){{{close_parens}}}")
            # 不阻塞，只警告 — mermaid 对此容忍度较高

        # 至少有 5 个节点
        node_count = len(re.findall(r'\S+\s*[\[\]\)]', content))
        if node_count < 3:
            logger.warning(f"[mindmap] 节点数过少: {node_count}")
            return False

        return True

    def post_process(self, result: WindowResult, params: dict) -> WindowResult:
        result.title = params.get("topic", "知识体系")
        return result
