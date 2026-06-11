"""练习题窗口 — 题目生成 + 答案自检

首选 Claude（推理能力强，生成的题目无歧义），回退 DeepSeek。
可选答案自检：用第二次 LLM 调用验证答案正确性。
"""

import json
import logging
from app.agents.windows.base import BaseWindow, WindowResult

logger = logging.getLogger(__name__)

EXERCISE_SYSTEM_PROMPT = """你是命题专家。根据知识点生成高质量的练习题。

## 命题要求
- 知识点：{topics}
- 难度：{difficulty}
- 题目数量：{count}

## 题型分布
- choice: 单选题（4个选项，1个正确答案）
- short_answer: 简答题（开放式，需有参考答案要点）
- case_analysis: 案例分析题（结合实际场景，需有分析要点）

## 题目质量标准
- 题干清晰无歧义，不能有多种理解方式
- 选择题的干扰项要有迷惑性但明确错误
- 答案必须唯一确定，解析要讲清楚为什么
- 难度标注要准确（入门/中等/进阶）
- 每道题标注对应的知识点 tag

## 输出格式
返回纯JSON（不要markdown标记）：
{{
    "exercises": [
        {{
            "id": "ex001",
            "type": "choice",
            "difficulty": "中等",
            "tags": ["知识点名"],
            "question": "题目内容",
            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
            "answer": "A",
            "explanation": "详细解析，解释为什么选A，为什么不选BCD"
        }}
    ]
}}

只返回JSON，不要其他文字。"""

# 答案自检提示词
ANSWER_CHECK_PROMPT = """你是命题审核专家。检查以下题目的答案是否正确。

题目和答案：
{exercise_json}

请判断：
1. 每道题的答案是否正确（是/否）
2. 选择题的干扰项是否合理（是/否）
3. 解析是否准确解释了答案（是/否）

返回JSON：
{{
    "all_correct": true/false,
    "issues": ["问题描述（如有）"],
    "fixed_exercises": [...]  // 如有错误，提供修正后的完整题目列表
}}

如果全部正确，issues 为空数组。只返回JSON。"""


class ExerciseWindow(BaseWindow):
    window_key = "exercise"
    window_label = "练习题"
    primary_model = "deepseek"   # Phase 6 可切换为 "claude"
    fallback_model = "qwen"
    temperature = 0.3
    max_tokens = 3500
    json_mode = True
    timeout = 120.0

    # 是否启用答案自检（可通过环境变量控制）
    enable_self_check: bool = True

    def build_prompt(self, params: dict) -> str:
        topics = ", ".join(params.get("topics", [])) or "基础知识"
        difficulty = params.get("difficulty", "中等")
        count = params.get("count", 5)
        return EXERCISE_SYSTEM_PROMPT.format(
            topics=topics, difficulty=difficulty, count=count
        )

    def validate(self, result: WindowResult) -> bool:
        content = result.content
        if not content:
            return False

        # content 已被 post_process 解析为 dict
        if not isinstance(content, dict):
            return False

        exercises = content.get("exercises", [])
        if not exercises or not isinstance(exercises, list):
            logger.warning("[exercise] exercises 为空或非列表")
            return False

        # 逐题检查必要字段
        required_fields = {"id", "type", "question", "answer", "explanation"}
        for i, ex in enumerate(exercises):
            missing = required_fields - set(ex.keys())
            if missing:
                logger.warning(f"[exercise] 第{i+1}题缺少字段: {missing}")
                return False
            # 选择题必须有 options
            if ex.get("type") == "choice" and not ex.get("options"):
                logger.warning(f"[exercise] 第{i+1}题选择题缺少 options")
                return False

        return True

    def post_process(self, result: WindowResult, params: dict) -> WindowResult:
        """解析 JSON，可选答案自检"""
        try:
            data = json.loads(result.content) if isinstance(result.content, str) else result.content
        except json.JSONDecodeError:
            logger.warning("[exercise] JSON 解析失败")
            data = {"exercises": []}

        # 答案自检
        if self.enable_self_check and data.get("exercises"):
            data = self._self_check(data)

        result.content = data
        result.title = params.get("title", f"{', '.join(params.get('topics', ['练习']))} 练习题")
        return result

    def _self_check(self, data: dict) -> dict:
        """用第二次 LLM 调用验证答案正确性"""
        try:
            exercise_json = json.dumps(data, ensure_ascii=False, indent=2)
            raw, model = self._try_call_with_fallback(
                ANSWER_CHECK_PROMPT.format(exercise_json=exercise_json)
            )
            check_content = raw.choices[0].message.content.strip()
            check_result = json.loads(check_content)

            if not check_result.get("all_correct", True):
                issues = check_result.get("issues", [])
                logger.warning(f"[exercise] 答案自检发现问题: {issues}")
                # 如果有修正版本，使用修正版
                fixed = check_result.get("fixed_exercises")
                if fixed:
                    logger.info("[exercise] 使用修正后的题目")
                    return {"exercises": fixed}

            logger.info("[exercise] 答案自检通过")
        except Exception as e:
            logger.warning(f"[exercise] 答案自检失败（使用原始结果）: {e}")

        return data
