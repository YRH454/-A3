"""Window 基类 — 每个资源类型窗口继承此类，实现独立的模型调用与校验"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

from app.services.llm import chat_deepseek, chat_qwen
from app.agents.shared.retry import with_retry, RateLimiter, run_with_timeout

logger = logging.getLogger(__name__)

# ─── 模型调用器注册 — 方便后续扩展 ──────────────────────

ModelCaller = Callable[..., Any]

MODEL_CALLERS: dict[str, ModelCaller] = {
    "deepseek": chat_deepseek,
    "qwen": chat_qwen,
}


def _lazy_import_claude():
    """延迟导入 Claude（避免 API key 未配置时报错）"""
    try:
        from app.services.llm import chat_claude
        return chat_claude
    except ImportError:
        return None


def _lazy_import_gemini():
    """延迟导入 Gemini"""
    try:
        from app.services.llm import chat_gemini
        return chat_gemini
    except ImportError:
        return None


def register_model(name: str, caller: ModelCaller) -> None:
    """注册新的模型调用器"""
    MODEL_CALLERS[name] = caller


def get_model_caller(name: str) -> ModelCaller:
    """获取模型调用器，按需加载 Claude/Gemini，找不到则回退到 deepseek"""
    if name in MODEL_CALLERS:
        return MODEL_CALLERS[name]

    # 延迟加载
    if name == "claude":
        caller = _lazy_import_claude()
        if caller:
            MODEL_CALLERS["claude"] = caller
            return caller
    elif name == "gemini":
        caller = _lazy_import_gemini()
        if caller:
            MODEL_CALLERS["gemini"] = caller
            return caller

    logger.warning(f"未知模型 '{name}'，回退到 deepseek")
    return chat_deepseek


# ─── WindowResult — 每个窗口统一的返回结构 ─────────────

@dataclass
class WindowResult:
    window_key: str
    label: str
    title: str = ""
    content: Any = None
    error: str = ""
    model_used: str = ""
    validated: bool = False
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        base: dict = {
            "type": self.window_key,
            "label": self.label,
            "title": self.title or self.label,
            "content": self.content,
        }
        if self.error:
            base["error"] = self.error
        if self.model_used:
            base["model_used"] = self.model_used
        return base


# ─── BaseWindow ──────────────────────────────────────────

class BaseWindow(ABC):
    """资源生成窗口基类。

    子类只需实现:
      - window_key: str       资源类型标识 (course/mindmap/...)
      - window_label: str     中文标签
      - primary_model: str    首选模型名
      - fallback_model: str   回退模型名
      - build_prompt(params)  构建提示词
      - validate(result)      结果校验
    """

    # ── 子类覆盖 ──
    window_key: str = ""
    window_label: str = ""
    primary_model: str = "deepseek"
    fallback_model: str = "deepseek"

    # ── LLM 调用参数 ──
    temperature: float = 0.5
    max_tokens: int = 2500
    json_mode: bool = False
    timeout: float = 90.0

    # ── 重试参数 ──
    max_retries: int = 2
    validate_retries: int = 1  # 校验失败后的重试次数

    def __init__(self):
        self._primary_limiter = RateLimiter.get(
            f"{self.window_key}_{self.primary_model}", max_concurrent=2
        )

    # ── 抽象方法 ──

    @abstractmethod
    def build_prompt(self, params: dict) -> str:
        """根据参数构建系统提示词"""
        ...

    @abstractmethod
    def validate(self, result: WindowResult) -> bool:
        """校验生成结果。返回 True 表示通过。"""
        ...

    # ── 模型调用 ──

    def _call_model(self, model_name: str, system_prompt: str) -> Any:
        """调用指定模型，带超时保护"""
        caller = get_model_caller(model_name)
        limiter = RateLimiter.get(f"{self.window_key}_{model_name}", max_concurrent=2)

        def _call():
            with limiter:
                return caller(
                    messages=[{"role": "system", "content": system_prompt}],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    json_mode=self.json_mode,
                )

        return run_with_timeout(_call, timeout=self.timeout)

    def _try_call_with_fallback(self, system_prompt: str) -> tuple[Any, str]:
        """首选模型调用，失败自动回退"""
        models_to_try = [self.primary_model]
        if self.fallback_model != self.primary_model:
            models_to_try.append(self.fallback_model)

        last_error = None
        for model_name in models_to_try:
            try:
                result = self._call_model(model_name, system_prompt)
                return result, model_name
            except Exception as e:
                last_error = e
                logger.warning(
                    f"[{self.window_key}] 模型 {model_name} 调用失败: {e}, "
                    f"尝试下一个..."
                )

        raise RuntimeError(
            f"[{self.window_key}] 所有模型调用失败, 最后错误: {last_error}"
        )

    # ── 结果提取 ──

    def extract_content(self, raw_response: Any) -> str:
        """从 LLM 响应中提取文本内容。子类可覆盖。"""
        try:
            return raw_response.choices[0].message.content.strip()
        except (AttributeError, IndexError, KeyError) as e:
            logger.error(f"[{self.window_key}] 提取内容失败: {e}")
            return ""

    # ── 主流程 ──

    def run(self, params: dict) -> WindowResult:
        """完整执行流程: 构建提示词 → 调用 LLM → 提取 → 校验 → 重试。

        params 由 Router 从 Orchestrator 的 plan 中传入。
        """
        system_prompt = self.build_prompt(params)
        logger.info(
            f"[{self.window_key}] 开始生成, 首选模型={self.primary_model}, "
            f"prompt_len={len(system_prompt)}"
        )

        # ── 调用 LLM ──
        try:
            raw_response, model_used = self._try_call_with_fallback(system_prompt)
        except Exception as e:
            logger.error(f"[{self.window_key}] 模型调用完全失败: {e}")
            return WindowResult(
                window_key=self.window_key,
                label=self.window_label,
                error=str(e),
            )

        content = self.extract_content(raw_response)

        # ── 构建结果 ──
        result = WindowResult(
            window_key=self.window_key,
            label=self.window_label,
            title=params.get("title", self.window_label),
            content=content,
            model_used=model_used,
        )

        # ── 解析（JSON mode 的窗口需要额外解析） ──
        result = self.post_process(result, params)

        # ── 校验 + 重试 ──
        for attempt in range(self.validate_retries + 1):
            if self.validate(result):
                result.validated = True
                break
            if attempt < self.validate_retries:
                logger.warning(
                    f"[{self.window_key}] 校验未通过, 第{attempt+1}次重试生成"
                )
                try:
                    raw_response, model_used = self._try_call_with_fallback(system_prompt)
                    content = self.extract_content(raw_response)
                    result.content = content
                    result.model_used = model_used
                    result = self.post_process(result, params)
                except Exception as e:
                    logger.error(f"[{self.window_key}] 重试失败: {e}")
                    break

        logger.info(
            f"[{self.window_key}] 完成, 模型={result.model_used}, "
            f"校验={'通过' if result.validated else '未通过'}, "
            f"错误={result.error or '无'}"
        )
        return result

    def post_process(self, result: WindowResult, params: dict) -> WindowResult:
        """后处理钩子。JSON mode 窗口覆盖此方法解析 content。"""
        return result
