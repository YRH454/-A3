"""教学视频窗口 — 分镜脚本 + AI视频生成Prompt

首选 Gemini（多模态场景理解），回退 DeepSeek。
可选集成 Seedance 实际生成视频（llm.py 已配置）。
"""

import json
import logging
from app.agents.windows.base import BaseWindow, WindowResult

logger = logging.getLogger(__name__)

MEDIA_SYSTEM_PROMPT = """你是教学视频导演。为知识点设计 3-5 分钟的短视频。

## 课程信息
- 主题：{topic}
- 目标观众：{level} 水平学生
- 重点内容：{focus}

## 视频设计要求
1. **分镜脚本**（Markdown 格式，含时间轴）
   - 开场（0:00-0:30）：吸引注意力，提出问题或展示应用场景
   - 核心讲解（0:30-2:30）：分 2-3 个要点，每点配画面描述
   - 案例演示（2:30-3:30）：具体例子或代码演示
   - 总结回顾（3:30-4:30）：要点回顾 + 下一步学习建议

2. **AI视频生成Prompt**（英文，用于 AI 视频生成工具如 Seedance/Sora）
   - 描述视频风格（如：clean educational animation, whiteboard style）
   - 场景氛围（如：modern classroom, soft lighting）
   - 关键视觉元素（如：animated diagrams, code overlay）

## 输出格式
返回纯JSON（不要markdown标记）：
{{
    "script": "完整的分镜脚本（Markdown格式，含时间轴和画面描述）",
    "seedance_prompt": "英文AI视频生成Prompt，50-150词，描述视频风格、场景、氛围和关键视觉元素"
}}

只返回JSON，不要其他文字。"""


class MediaWindow(BaseWindow):
    window_key = "media"
    window_label = "教学视频脚本"
    primary_model = "deepseek"   # Phase 6 可切换为 "gemini"
    fallback_model = "qwen"
    temperature = 0.6
    max_tokens = 3000
    json_mode = True
    timeout = 120.0

    def build_prompt(self, params: dict) -> str:
        topic = params.get("topic", "学习内容")
        level = params.get("level", "初级")
        focus = params.get("focus", "核心概念")
        return MEDIA_SYSTEM_PROMPT.format(topic=topic, level=level, focus=focus)

    def validate(self, result: WindowResult) -> bool:
        content = result.content
        if not content or not isinstance(content, dict):
            return False

        # 必须有 script 字段
        script = content.get("script", "")
        if not script or len(script) < 100:
            logger.warning(f"[media] script 过短或缺失: {len(script)}字")
            return False

        # seedance_prompt 可选但推荐有
        if not content.get("seedance_prompt"):
            logger.info("[media] 未生成 seedance_prompt（非致命）")

        return True

    def post_process(self, result: WindowResult, params: dict) -> WindowResult:
        """解析 JSON，可选触发 Seedance 实际生成"""
        try:
            data = json.loads(result.content) if isinstance(result.content, str) else result.content
        except json.JSONDecodeError:
            logger.warning("[media] JSON 解析失败")
            data = {
                "script": "## 视频脚本\n\n脚本生成失败，请重试。",
                "seedance_prompt": "",
            }

        result.content = data
        result.title = params.get("topic", "教学视频")

        # 可选：调用 Seedance 生成视频
        seedance_prompt = data.get("seedance_prompt", "")
        if seedance_prompt and params.get("_generate_video"):
            try:
                video_result = self._call_seedance(seedance_prompt)
                result.metadata["seedance_result"] = video_result
                logger.info("[media] Seedance 视频生成已触发")
            except Exception as e:
                logger.warning(f"[media] Seedance 调用失败: {e}")
                result.metadata["seedance_error"] = str(e)

        return result

    def _call_seedance(self, prompt: str) -> dict:
        """调用 Seedance API 生成视频（llm.py 已配置）"""
        from app.services.llm import seedance, SEEDANCE_MODEL

        resp = seedance.chat.completions.create(
            model=SEEDANCE_MODEL or "seedance",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        return {
            "model": SEEDANCE_MODEL,
            "prompt": prompt,
            "response": resp.choices[0].message.content.strip() if resp.choices else "",
        }
